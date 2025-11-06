from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from Base import Lesson, Material, Course, User
from basemodels import LessonCreate, MaterialCreate


# -------------------- 1️⃣ Get All Mentors --------------------
def get_all_mentors(db: Session):
    """
    Fetch all users with role 'mentor'
    """
    mentors = db.query(User).filter(User.role == "mentor").all()
    if not mentors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mentors found"
        )
    return mentors


# -------------------- 2️⃣ Get Courses by Mentor --------------------
def get_courses_by_mentor(db: Session, mentor_id: int):
    mentor = db.query(User).filter(User.id == mentor_id, User.role == "mentor").first()
    if not mentor:
        return None

    # ✅ Fetch courses by mentor_id
    courses = db.query(Course).filter(Course.mentor_id == mentor_id).all()

    result = {
        "mentor_id": mentor.id,
        "mentor_name": f"{mentor.first_name} {mentor.last_name or ''}".strip(),
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "language": c.language,
                "mentor": {
                    "id": mentor.id,
                    "first_name": mentor.first_name,
                    "last_name": mentor.last_name,
                    "email": mentor.email,
                    "role": mentor.role.value if hasattr(mentor.role, "value") else mentor.role,
                },
            }
            for c in courses
        ],
    }

    return result


# -------------------- 3️⃣ Assign Student to Mentor --------------------
def assign_student_to_mentor(db: Session, mentor_id: int, student_id: int):
    """
    Assign a student to a mentor (many-to-many relationship).
    """
    mentor = db.query(User).filter(User.id == mentor_id, User.role == "mentor").first()
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()

    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Prevent duplicate assignment
    if student in mentor.supervised_students:
        raise HTTPException(status_code=400, detail="Student is already assigned to this mentor")

    mentor.supervised_students.append(student)
    db.commit()
    db.refresh(mentor)

    return {
        "message": f"Student '{student.first_name}' assigned to mentor '{mentor.first_name}' successfully.",
        "mentor_id": mentor.id,
        "student_id": student.id
    }


# -------------------- 4️⃣ Get Students Assigned to a Mentor --------------------
def get_students_by_mentor(db: Session, mentor_id: int):
    """
    Returns all students supervised by a mentor, excluding sensitive data.
    """
    mentor = db.query(User).filter(User.id == mentor_id, User.role == "mentor").first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    # ✅ Only include safe fields
    def safe_student_dict(student):
        return {
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "role": student.role,
            "is_active": student.is_active
        }

    return {
        "mentor": {
            "id": mentor.id,
            "first_name": mentor.first_name,
            "last_name": mentor.last_name,
            "email": mentor.email
        },
        "students": [safe_student_dict(student) for student in mentor.supervised_students]
    }