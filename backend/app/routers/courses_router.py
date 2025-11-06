from fastapi import APIRouter, Depends, Query,HTTPException,status
from sqlalchemy.orm import Session
from typing import Dict, List
from pydantic import BaseModel
from fastapi import UploadFile, File,Form
import uuid
import os
from app.crud.courses_crud import (
    create_course,
    get_course_by_id,
    get_all_unpublished_courses,
    delete_course,
    update_course,
    update_course_status,
    upload_to_minio
)
from basemodels import CourseBase, CourseUpdate,CourseOut
from database import get_db
from Base import PublishStatusEnum, Course,UserRole
from app.crud.auth import get_current_user
from Base import User

router = APIRouter()


# ===========================================
# GET: Courses Dashboard
# ===========================================
# =====================================================
# Utility function to build public MinIO URLs
# =====================================================
def get_public_banner_url(path: str) -> str:
    """
    Convert stored MinIO file path to public URL
    Example: 'course-banners/banners/image.jpg'
    → 'http://127.0.0.1:9000/course-banners/banners/image.jpg'
    """
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return f"http://127.0.0.1:9000/{path}"  # Replace with your MinIO base URL


# =====================================================
# 1️⃣ Dashboard: Get All Courses with Mentor Info
# =====================================================
@router.get("/courses")
def get_all_courses(db: Session = Depends(get_db)):
    """
    Returns list of all courses with mentor, publish status, and banner image.
    """
    courses = db.query(Course).all()
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found")

    result = []
    for c in courses:
        mentor = db.query(User).filter(User.id == c.mentor_id).first()
        mentor_name = f"{mentor.first_name} {mentor.last_name or ''}".strip() if mentor else "Unknown"

        total_students = len(getattr(c, "students", [])) if hasattr(c, "students") else 0

        result.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "language": c.language,
            "batch": c.batch,
            "mentor_name": mentor_name,
            # "publish_status": c.publish_status.value if hasattr(c.publish_status, "value") else str(c.publish_status),
            # "active": c.publish_status == PublishStatus.published,
            "banner_url": get_public_banner_url(c.banner_url),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "students": total_students
        })

    return {"total_courses": len(result), "courses": result}





# # ------------------ GET ALL COURSES ------------------ #
# @router.get("/", response_model=List[CourseOut])
# def get_courses(db: Session = Depends(get_db)):
#     """
#     Fetch all courses.
#     """
#     return db.query(Course).all()
@router.post("/create")
def create_course_endpoint(
    title: str = Form(...),
    description: str = Form(""),
    language: str = Form("English"),
    # mentor_id: int = Form(...),
    # batch: str = Form(None),
    banner_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user),  # 👈 Authenticated user from JWT
):
    """
    🧱 Create a new course (only Mentor or Admin allowed).
    """

    # # ✅ Step 1: Verify user role
    # if current_user.role not in [UserRole.admin, UserRole.mentor]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only mentors or admins can create courses."
    #     )

    # # ✅ Step 2: If mentor is creating, ensure mentor_id matches their own user_id
    # if current_user.role == UserRole.mentor and current_user.id != mentor_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Mentors can only create courses for themselves."
        # )

    # ✅ Step 3: Build course data
    course_data = CourseBase(
        title=title,
        description=description,
        language=language,
        # mentor_id=mentor_id,
        banner_url=None,
        # batch=batch,
    )

    # ✅ Step 4: Create the course
    new_course = create_course(course_data, db, banner_file)
    return {"message": "Course created successfully", "course": new_course}


# ------------------ UPDATE COURSE ------------------ #
@router.put("/courses/{course_id}")
async def update_course_route(
    course_id: int,
    title: str = Form(None),
    description: str = Form(None),
    language: str = Form(None),
    banner_file: UploadFile = None,
    db: Session = Depends(get_db),
):
    data = CourseUpdate(title=title, description=description, language=language)
    return update_course(db, course_id, data, banner_file)


# ------------------ DELETE COURSE ------------------ #
@router.delete("/delete/{course_id}")
def delete_course_endpoint(course_id: int, db: Session = Depends(get_db)):
    """
    Delete a course by ID (no auth required).
    """
    return delete_course(course_id, db)





# ------------------ GET COURSE BY ID ------------------ #
@router.get("/{course_id}", summary="Get a single course by ID")
def get_course(course_id: int, db: Session = Depends(get_db)):
    """
    Get course details by ID (with modules and lessons).
    """
    return get_course_by_id(course_id, db)


# ------------------ GET ALL UNPUBLISHED COURSES ------------------ #
@router.get("/unpublished/all", summary="Get all unpublished courses")
def list_unpublished_courses(db: Session = Depends(get_db)):
    """
    Fetch all courses that are not yet published.
    """
    return get_all_unpublished_courses(db)


# ------------------ UPDATE COURSE STATUS ------------------ #
@router.put("/{course_id}/status", summary="Update course publish status")
def change_course_status(
    course_id: int,
    new_status: PublishStatusEnum = Query(..., description="New status: draft, published, unpublished"),
    db: Session = Depends(get_db),
):
    """
    Update a course's publish status (no auth required).
    """
    return update_course_status(db, course_id, new_status)

@router.put("/update-banner/{course_id}")
def update_course_banner(
    course_id: int,
    banner_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Update or replace a course banner image.
    Automatically uploads the new banner to MinIO (with versioning).
    """
    # ✅ Fetch the course
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found")

    try:
        # ✅ Upload new banner to MinIO (versioned)
        banner_url = upload_to_minio(banner_file)

        # ✅ Update database record
        db_course.banner_url = banner_url
        db.commit()
        db.refresh(db_course)

        return {
            "message": "✅ Banner updated successfully",
            "course_id": db_course.id,
            "title": db_course.title,
            "banner_url": db_course.banner_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update banner: {str(e)}")
    
