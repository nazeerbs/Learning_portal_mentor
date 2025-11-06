from fastapi import (
    APIRouter, Depends, UploadFile, File, HTTPException, Form
)
from sqlalchemy.orm import Session,joinedload
from app.crud import evaluation_crud
from database import get_db
from Base import Submission,User,Certification
from basemodels import FeedbackCreate, SubmissionResponse
from typing import List
from app.crud.certificate_generator import generate_certificate
from datetime import datetime
from app.crud.evaluation_crud import get_leaderboard
from app.crud.evaluation_crud import recalculate_leaderboard_and_certification
# ============================================================
# 📘 Router Setup
# ============================================================
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


# ============================================================
# 📝 CREATE SUBMISSION (AI GRADING)
# ============================================================
@router.post("/create")
async def create_submission(
    assignment_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = None,
    db: Session = Depends(get_db)
):
    """
    Student uploads assignment → AI automatically grades it.
    """
    try:
        submission_data = type("obj", (object,), {
            "assignment_id": assignment_id,
            "student_id": student_id
        })

        result = await evaluation_crud.create_submission(db, submission_data, file)

        return {
            "message": "Submission uploaded & graded successfully",
            "submission": {
                "id": result.id,
                "ai_score": result.ai_score,
                "ai_feedback": result.ai_feedback
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 📄 VIEW ALL SUBMISSIONS
# ============================================================
@router.get("/", response_model=List[SubmissionResponse])
def get_all_submissions(db: Session = Depends(get_db)):
    """
    Fetch all submissions from the database.
    """
    submissions = db.query(Submission).all()
    return submissions


# ============================================================
# 📄 VIEW SUBMISSIONS (FILTERED)
# ============================================================
@router.get("/submissions")
def list_submissions(assignment_id: int = None, db: Session = Depends(get_db)):
    """
    Get all submissions (optionally filter by assignment_id).
    """
    return evaluation_crud.get_submissions(db, assignment_id)


# ============================================================
# 🔍 VIEW SINGLE SUBMISSION
# ============================================================
@router.get("/submission/{submission_id}")
def view_submission(submission_id: int, db: Session = Depends(get_db)):
    """
    View a specific submission by ID.
    """
    submission = evaluation_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.post("/submission/{submission_id}/grade")
def grade_submission(
    submission_id: int,
    mentor_score: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    🧮 Mentor manually grades a submission.
    Generates certificate if score >= 80.
    """
    try:
        # 1️⃣ Update mentor score and recalculate leaderboard
        submission = evaluation_crud.update_score(db, submission_id, mentor_score)
        recalculate_leaderboard_and_certification(db, student_id=submission.student_id)

        certificate_url = None
        certificate_status = "Not Qualified"

        # 2️⃣ Generate certificate if score >= 80
        if mentor_score >= 8:
            student = db.query(User).filter(User.id == submission.student_id).first()
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")

            # Generate PDF in MinIO
            certificate_url = generate_certificate(
                f"{student.first_name} {student.last_name}",
                "Course Completion"
            )

            # Save in Certification table
            cert = db.query(Certification).filter(Certification.student_id == student.id).first()
            if not cert:
                cert = Certification(student_id=student.id)
                db.add(cert)

            cert.certificate_status = "Qualified"
            cert.issue_date = datetime.utcnow()
            cert.file_url = certificate_url  # ✅ Correct field name
            db.commit()
            db.refresh(cert)
            certificate_status = "Qualified"

        else:
            # 3️⃣ Not qualified → clear previous certificate if any
            cert = db.query(Certification).filter(Certification.student_id == submission.student_id).first()
            if cert:
                cert.certificate_status = "Not Qualified"
                cert.issue_date = None
                cert.file_url = None  # ✅ correct field
                db.commit()

        # 4️⃣ Return success response
        return {
            "message": "✅ Mentor grade updated successfully",
            "submission": {
                "id": submission.id,
                "mentor_score": submission.mentor_score,
                "student_id": submission.student_id,
                "updated_at": datetime.utcnow().isoformat(),
            },
            "leaderboard_update": True,
            "certificate_status": certificate_status,
            "certificate_url": certificate_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mentor grading failed: {e}")

# ============================================================
# 💬 MENTOR FEEDBACK (TEXT / AUDIO / VIDEO)
# ============================================================
@router.post("/submission/{submission_id}/feedback")
def feedback_submission(
    submission_id: int,
    mentor_id: int = Form(...),
    feedback_type: str = Form(...),
    file: UploadFile = File(None),
    text: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Mentor adds feedback (text, audio, or video).
    """
    if feedback_type in ["audio", "video"] and file:
        feedback_content = evaluation_crud.save_media_file(file)
    elif feedback_type == "text" and text:
        feedback_content = text
    else:
        raise HTTPException(status_code=400, detail="Invalid feedback input")

    feedback = FeedbackCreate(
        submission_id=submission_id,
        mentor_id=mentor_id,
        feedback_type=feedback_type,
        feedback_content=feedback_content
    )

    result = evaluation_crud.add_feedback(db, submission_id, feedback)
    return {
        "message": "Feedback added successfully",
        "feedback": {
            "id": result.id,
            "feedback_type": result.feedback_type,
            "feedback_content": result.feedback_content
        }
    }
@router.get("/leaderboard")
def leaderboard(order: str = "asc", db: Session = Depends(get_db)):
    """
    Retrieve leaderboard records.
    - order: 'asc' (default) or 'desc'
    """
    try:
        records = get_leaderboard(db, order)
        if not records:
            return {"message": "No leaderboard data found."}

        return {
            "message": "Leaderboard fetched successfully.",
            "order": order,
            "data": [
                {
                    "student_id": r.student_id,
                    "total_score": r.total_score,
                    "average_score": r.average_score,
                    "total_assignments": r.total_assignments,
                    "rank": r.rank,
                }
                for r in records
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


## ============================================================
# 🧩 MENTOR FULL REVIEW (GRADE + TEXT FEEDBACK ONLY)
# ============================================================
@router.post("/submission/{submission_id}/full-review")
async def full_review_submission(
    submission_id: int,
    mentor_id: int = Form(...),
    mentor_score: int = Form(...),
    feedback_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Mentor performs a full review:
    - Updates mentor grade
    - Adds text feedback (no file upload)
    """
    try:
        # ✅ Step 1: Update mentor score
        submission = evaluation_crud.update_score(db, submission_id, mentor_score)

        # ✅ Step 2: Create feedback record (text only)
        feedback_data = FeedbackCreate(
            submission_id=submission_id,
            mentor_id=mentor_id,
            feedback_type="text",
            feedback_content=feedback_text
        )

        feedback = evaluation_crud.add_feedback(db, submission_id, feedback_data)

        # ✅ Step 3: Return combined response
        return {
            "message": "Full review (grade + feedback) completed successfully",
            "submission": {
                "id": submission.id,
                "mentor_score": submission.mentor_score,
                "ai_score": submission.ai_score,
            },
            "feedback": {
                "id": feedback.id,
                "feedback_type": feedback.feedback_type,
                "feedback_content": feedback.feedback_content
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# @router.get("/submission/{submission_id}")
# def get_submission(submission_id: int, db: Session = Depends(get_db)):
#     submission = db.query(Submission).filter(Submission.id == submission_id).first()
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")

#     student = db.query(User).filter(User.id == submission.student_id).first()
#     return {
#         "id": submission.id,
#         "student_name": student.name if student else "Unknown",
#         "project_name": submission.project_name,
#         "code": submission.code,
#         "plagiarism_score": submission.plagiarism_score or 0,
#         "ai_summary": submission.ai_summary or "No AI summary available",
#     }
# ============================================================
# 📄 VIEW SUBMISSION FOR PREVIEW
# ============================================================
@router.get("/submission/{submission_id}")
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {
        "id": submission.id,
        "file_url": f"http://127.0.0.1:8000/{submission.file_path}",
        "ai_score": submission.ai_score,
        "ai_feedback": submission.ai_feedback,
    }


# ============================================================
# 🧾 MENTOR GRADE + FEEDBACK
# ============================================================
@router.post("/submission/{submission_id}/full-review")
def full_review_submission(
    submission_id: int,
    mentor_id: int = Form(...),
    mentor_score: int = Form(...),
    feedback_text: str = Form(...),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Update mentor score
    submission.mentor_score = mentor_score
    db.commit()

    feedback = FeedbackCreate(
        submission_id=submission_id,
        mentor_id=mentor_id,
        feedback_type="text",
        feedback_content=feedback_text,
    )
    evaluation_crud.add_feedback(db, submission_id, feedback)

    return {"message": "Full review completed successfully"}

@router.get("/submissions/list")
def list_submissions(db: Session = Depends(get_db)):
    submissions = db.query(Submission).options(joinedload(Submission.student)).all()

    result = []
    for s in submissions:
        student = getattr(s, "student", None)
        if student:
            learner_name = " ".join(
                [n for n in [student.first_name, student.last_name] if n]
            ).strip() or "Unknown"
        else:
            learner_name = "Unknown"

        result.append({
            "id": s.id,
            "learner_name": learner_name
        })

    return result