from sqlalchemy.orm import Session
from Base import Course, Submission, Feedback, Leaderboard, Certification, User
from app.crud.certificate_generator import generate_certificate
from basemodels import FeedbackCreate
from datetime import datetime, timezone
from typing import Optional, Tuple, List
import os
import aiofiles
from PyPDF2 import PdfReader
from fastapi import UploadFile
import re
import openai
from dotenv import load_dotenv
import re
import google.generativeai as genai
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===================================================
# 💾 Save uploaded media file (audio/video feedback)
# ===================================================
def save_media_file(file, media_dir="media/"):
    """Save uploaded feedback media (audio/video) to local directory."""
    ext = file.filename.split(".")[-1]
    filename = f"{datetime.utcnow().timestamp()}.{ext}"
    os.makedirs(media_dir, exist_ok=True)
    filepath = os.path.join(media_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return filepath


# ===================================================
# 📁 Save uploaded submission file
# ===================================================
async def save_uploaded_file(file, upload_dir="uploads/submissions"):
    """Save uploaded assignment file asynchronously."""
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{datetime.utcnow().timestamp()}.{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return file_path


# ===================================================
# 📝 Create Submission + AI Grading
# ===================================================
async def create_submission(db: Session, submission_data, file):
    """
    Create a new submission entry, upload file, and trigger AI grading.
    """
    try:
        # 1️⃣ Save file
        file_url = await save_uploaded_file(file) if file else None

        # 2️⃣ Create initial submission
        new_submission = Submission(
            assignment_id=submission_data.assignment_id,
            student_id=submission_data.student_id,
            file_url=file_url,
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        # 3️⃣ Run AI grading
        ai_score, ai_feedback = grade_assignment_ai(file_url, submission_data.student_id)

        # 4️⃣ Update submission with AI feedback
        new_submission.ai_score = ai_score
        new_submission.ai_feedback = ai_feedback
        db.commit()
        db.refresh(new_submission)

        return new_submission

    except Exception as e:
        raise Exception(f"Failed to create submission: {e}")


# ===================================================
# 🔍 Retrieve Submissions
# ===================================================
def get_submission(db: Session, submission_id: int) -> Optional[Submission]:
    """Retrieve a single submission by ID."""
    return db.query(Submission).filter(Submission.id == submission_id).first()


def get_submissions(db: Session, student_id: Optional[int] = None) -> List[Submission]:
    """Retrieve all submissions (optionally filtered by student ID)."""
    q = db.query(Submission)
    if student_id is not None:
        q = q.filter(Submission.student_id == student_id)
    return q.all()


# ===================================================
# 💬 Add Feedback
# ===================================================
def add_feedback(db: Session, submission_id: int, feedback: FeedbackCreate):
    """Add text/audio/video feedback to a specific submission."""
    new_feedback = Feedback(
        submission_id=submission_id,
        mentor_id=feedback.mentor_id,
        feedback_type=feedback.feedback_type,
        feedback_content=feedback.feedback_content,
        created_at=datetime.utcnow(),
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback


# ===================================================
# 🧮 SCORE, LEADERBOARD & CERTIFICATION LOGIC
# ===================================================
def _compute_submission_effective_score(sub: Submission) -> int:
    """Return mentor_score if exists, else ai_score, else 0."""
    if sub.mentor_score is not None:
        return int(sub.mentor_score)
    if sub.ai_score is not None:
        return int(sub.ai_score)
    return 0


def _recalculate_student_stats(db: Session, student_id: int) -> Tuple[int, float, int]:
    """Recalculate total_score, average_score, and total_assignments."""
    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    total_assignments = len(submissions)

    if total_assignments == 0:
        return 0, 0.0, 0

    total_score = sum(_compute_submission_effective_score(s) for s in submissions)
    average_score = total_score / total_assignments if total_assignments > 0 else 0.0
    return total_score, average_score, total_assignments


def _update_leaderboard_row(db: Session, student_id: int, total_score: int, average_score: float, total_assignments: int):
    """Update or create leaderboard record for the given student."""
    lb = db.query(Leaderboard).filter(Leaderboard.student_id == student_id).first()
    if not lb:
        lb = Leaderboard(
            student_id=student_id,
            total_score=total_score,
            average_score=average_score,
            total_assignments=total_assignments,
        )
        db.add(lb)
    else:
        lb.total_score = total_score
        lb.average_score = average_score
        lb.total_assignments = total_assignments

    db.flush()


def _recompute_all_ranks(db: Session):
    """Recalculate leaderboard ranks (dense rank based on total_score)."""
    rows = db.query(Leaderboard).order_by(Leaderboard.total_score.desc(), Leaderboard.student_id).all()
    last_score = None
    dense_rank = 0

    for idx, row in enumerate(rows, start=1):
        if last_score is None or row.total_score != last_score:
            dense_rank = idx
        row.rank = dense_rank
        last_score = row.total_score


def _update_certification_for_student(db: Session, student_id: int, average_score: float, qualification_threshold: int = 80):
    """
    Update or create certification(s) for student based on average score.
    If average >= threshold → Qualified + generate and save certificate.
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        return

    cert = db.query(Certification).filter(Certification.student_id == student_id).first()
    if not cert:
        cert = Certification(student_id=student_id)
        db.add(cert)

    if average_score >= qualification_threshold:
        cert.certificate_status = "Qualified"
        cert.issue_date = cert.issue_date or datetime.utcnow()

        # ✅ Generate and save certificate
        from app.crud.certificate_generator import generate_certificate
        certificate_url = generate_certificate(f"{student.first_name} {student.last_name}", "General Qualification")

        cert.certificate_url = certificate_url  # <-- Save URL to DB

    else:
        cert.certificate_status = "Not Qualified"
        cert.issue_date = None
        cert.certificate_url = None

    db.commit()
    db.refresh(cert)


def recalculate_leaderboard_and_certification(db: Session, student_id: Optional[int] = None):
    """Recalculate leaderboard and certification for one or all students."""
    if student_id is not None:
        total_score, avg_score, total_assignments = _recalculate_student_stats(db, student_id)
        _update_leaderboard_row(db, student_id, total_score, avg_score, total_assignments)
        _update_certification_for_student(db, student_id, avg_score)
    else:
        student_ids = [row[0] for row in db.query(Submission.student_id).distinct()]
        for sid in student_ids:
            total_score, avg_score, total_assignments = _recalculate_student_stats(db, sid)
            _update_leaderboard_row(db, sid, total_score, avg_score, total_assignments)
            _update_certification_for_student(db, sid, avg_score)

    _recompute_all_ranks(db)
    db.commit()


def update_score(db: Session, submission_id: int, mentor_score: int):
    """Update mentor_score and recalculate leaderboard & certification."""
    sub = get_submission(db, submission_id)
    if not sub:
        raise ValueError(f"Submission id {submission_id} not found")

    sub.mentor_score = int(mentor_score)
    db.add(sub)
    db.flush()
    recalculate_leaderboard_and_certification(db, student_id=sub.student_id)
    db.refresh(sub)
    return sub


def get_leaderboard(db: Session, order: str = "asc"):
    """Retrieve leaderboard records ordered by rank."""
    query = db.query(Leaderboard)
    if order.lower() == "desc":
        query = query.order_by(Leaderboard.rank.desc())
    else:
        query = query.order_by(Leaderboard.rank.asc())
    return query.all()


# ===================================================
# 🤖 AI Grading Logic
# ===================================================
# def grade_assignment_ai(file_path: str, student_id: int):
#     """
#     Evaluate assignment using OpenAI GPT.
#     Returns (score, feedback).
#     If API quota or error occurs → return score=0 with the exact error message.
#     """
#     try:
#         prompt = (
#             f"Evaluate the following assignment submission for student ID {student_id}.\n"
#             f"Give a numeric score (0–100) and one-line feedback.\n"
#             f"File path: {file_path}"
#         )

#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are an AI that grades assignments accurately."},
#                 {"role": "user", "content": prompt},
#             ],
#         )

#         ai_feedback = completion.choices[0].message.content.strip()
#         match = re.search(r"(\d{1,3})", ai_feedback)
#         ai_score = min(int(match.group(1)), 10) if match else 0

#         return ai_score, ai_feedback

#     except Exception as e:
#         # Return 0 score and show quota or API error message
#         return 0, f"AI grading failed due to: {e}"


# Configure Gemini API key
from PyPDF2 import PdfReader
from docx import Document

# ✅ Load API key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text content from a variety of file types.
    Supports: .py, .txt, .java, .c, .cpp, .pdf, .docx
    """
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in [".py", ".txt", ".java", ".c", ".cpp", ".js", ".html", ".css"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".pdf":
            text = ""
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text

        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])

        else:
            return f"[Unsupported file type: {ext}]"

    except Exception as e:
        return f"[Error reading file: {e}]"


def grade_assignment_ai(file_path: str, student_id: int):
    """
    Evaluate any assignment file using Google Gemini.
    Reads content (text/code/PDF/DOCX) and sends it to the model.
    Returns (score, feedback).
    """
    try:
        # ✅ Extract content from any supported file
        file_content = extract_text_from_file(file_path)

        prompt = (
            f"Evaluate the following student assignment (ID: {student_id}).\n"
            f"Give a numeric score (0–100) and a one-line feedback.\n\n"
            f"--- Assignment Content ---\n{file_content}\n"
            f"---------------------------"
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        ai_feedback = response.text.strip()

        # ✅ Extract numeric score (0–100)
        match = re.search(r"(\d{1,3})", ai_feedback)
        ai_score = min(int(match.group(1)), 100) if match else 0

        return ai_score, ai_feedback

    except Exception as e:
        return 0, f"AI grading failed due to: {e}"