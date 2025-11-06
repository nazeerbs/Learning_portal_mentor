from fastapi import Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict
from basemodels import CourseBase, CourseUpdate
from Base import Course, PublishStatusEnum, Module,  User
from database import get_db
from minio import Minio
import uuid
import io
import os
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig
from dotenv import load_dotenv
from datetime import datetime, timezone

# ✅ Load environment variables
load_dotenv()

# ✅ Read from .env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

# ✅ Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

# ---------------------- GET ALL COURSES ----------------------

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    """
    Fetch all courses (paginated).
    """
    return db.query(Course).offset(skip).limit(limit).all()


def upload_to_minio(file: UploadFile) -> str:
    """
    Upload a file to MinIO and return its versioned public URL.
    Keeps original filename; MinIO will version it automatically.
    """
    try:
        # ✅ Ensure bucket exists and versioning is enabled
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)

        minio_client.set_bucket_versioning(
            MINIO_BUCKET_NAME,
            VersioningConfig(ENABLED)
        )

        # ✅ Keep original file name (inside banners folder)
        object_name = f"banners/{file.filename}"

        # ✅ Upload the file
        file_data = io.BytesIO(file.file.read())
        file_data.seek(0)

        result = minio_client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            file_data,
            length=len(file_data.getvalue()),
            content_type=file.content_type
        )

        # ✅ Construct versioned file URL
        # Note: The version ID can be retrieved from the `result.version_id`
        version_id = getattr(result, "version_id", None)
        public_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"
        if version_id:
            public_url += f"?versionId={version_id}"

        return public_url

    except Exception as e:
        print("❌ MinIO upload error:", str(e))
        raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")
def create_course(
    course_data: CourseBase,
    db: Session = Depends(get_db),
    banner_file: UploadFile = File(None)
) -> dict:
    """
    Create a new course with optional banner upload.
    """

    # # 🧩 1. Validate mentor
    # if not getattr(course_data, "mentor_id", None):
    #     raise HTTPException(status_code=400, detail="mentor_id is required to create a course")

    # mentor = db.query(User).filter(User.id == course_data.mentor_id, User.role == "mentor").first()
    # if not mentor:
    #     raise HTTPException(status_code=404, detail="Mentor not found or not a mentor")

    # 🚫 2. Prevent duplicate course titles for the same mentor
    existing_course = (
        db.query(Course)
        .filter(
            Course.title == course_data.title,
            # Course.mentor_id == course_data.mentor_id
        )
        .first()
    )
    if existing_course:
        raise HTTPException(status_code=409, detail="Course already exists for this mentor")

    # 🖼️ 3. Handle banner upload (optional)
    banner_url = None
    if banner_file:
        try:
            banner_url = upload_to_minio(banner_file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")

    # 🏗️ 4. Create Course record
    try:
        db_course = Course(
            title=course_data.title,
            description=course_data.description or "",
            language=course_data.language or "English",
            # mentor_id=course_data.mentor_id,
            banner_url=banner_url,
            # batch=course_data.batch if hasattr(course_data, "batch") else None,
           
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        db.add(db_course)
        db.commit()
        db.refresh(db_course)

        # mentor_name = f"{mentor.first_name} {mentor.last_name or ''}".strip()

        return {
            "message": "✅ Course created successfully",
            "id": db_course.id,
            "title": db_course.title,
            "description": db_course.description,
            "language": db_course.language,
            "banner_url": db_course.banner_url,
            "publish_status": db_course.publish_status.value,
            "batch": db_course.batch,
            # "mentor_id": mentor.id,
            # "mentor_name": mentor_name,
            "created_at": db_course.created_at.isoformat(),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database integrity error during course creation")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
def update_course(db: Session, course_id: int, course_data: CourseUpdate, banner_file: UploadFile = None) -> Dict:
    """
    Update an existing course by ID.
    If banner_file is provided, upload to MinIO and update banner_url.
    """
    # 🔍 Check if the course exists
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found")

    # 🚫 Prevent duplicate title (ignore current course)
    duplicate_course = (
        db.query(Course)
        .filter(Course.title == course_data.title, Course.id != course_id)
        .first()
    )
    if duplicate_course:
        raise HTTPException(
            status_code=409,
            detail=f"Another course with title '{course_data.title}' already exists"
        )

    # 🖼️ Upload new banner (if provided)
    if banner_file:
        try:
            filename = f"banner_{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            file_data = banner_file.file

            # Upload to MinIO bucket
            minio_client.put_object(
                MINIO_BUCKET_NAME,
                filename,
                file_data,
                length=-1,
                part_size=10 * 1024 * 1024,
                content_type=banner_file.content_type,
            )

            # Public URL (assuming MinIO runs locally)
            banner_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{filename}"
            db_course.banner_url = banner_url

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")

    # 🧱 Update other allowed fields
    db_course.title = course_data.title or db_course.title
    db_course.description = course_data.description or db_course.description
    db_course.language = course_data.language or db_course.language
    db_course.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(db_course)
        return {
            "message": "✅ Course updated successfully",
            "course": {
                "id": db_course.id,
                "title": db_course.title,
                "description": db_course.description,
                "language": db_course.language,
                "banner_url": db_course.banner_url,
                "updated_at": db_course.updated_at.isoformat(),
            },
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation during update")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error during update: {str(e)}")

# ---------------------- DELETE COURSE ----------------------

def delete_course(course_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Delete a course by ID.
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found")

    db.delete(db_course)
    db.commit()
    return {"message": f"Course with ID {course_id} deleted successfully"}


# ---------------------- GET COURSE BY ID ----------------------

def get_course_by_id(course_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Retrieve a course with all its modules, lessons, and projects.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found")

    modules_data = []
    for module in list(course.modules or []):
        lessons_data = []
        for lesson in list(module.lessons or []):
            lesson_materials = [
                {
                    "id": m.id,
                    "file_name": m.file_name,
                    "file_url": m.file_url,
                    "status": m.status,
                    "uploaded_at": m.uploaded_at
                }
                for m in list(lesson.materials or [])
                if getattr(m, "status", None) == "approved"
            ]

            lessons_data.append({
                "id": lesson.id,
                "title": lesson.title,
                "description": getattr(lesson, "description", None),
                "content_type": getattr(lesson, "content_type", None),
                "content_url": getattr(lesson, "content_url", None),
                "language": getattr(lesson, "language", None),
                "materials": lesson_materials
            })

        modules_data.append({
            "id": module.id,
            "title": module.title,
            "position": getattr(module, "position", None),
            "lessons": lessons_data
        })

    projects_data = []
    for p in list(getattr(course, "projects", []) or []):
        if getattr(p, "status", None) != "approved":
            continue

        project_files = [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_url": f.file_url,
                "status": f.status,
                "uploaded_at": f.uploaded_at
            }
            for f in list(getattr(p, "files", []) or [])
        ]

        projects_data.append({
            "id": p.id,
            "course_id": getattr(p, "course_id", None),
            "title": getattr(p, "title", None),
            "description": getattr(p, "description", None),
            "requirements": getattr(p, "requirements", None),
            "due_date": getattr(p, "due_date", None),
            "files": project_files
        })

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "language": course.language,
        "publish_status": course.publish_status,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        "modules": modules_data,
        "projects": projects_data
    }


# ---------------------- GET ALL UNPUBLISHED COURSES ----------------------

def get_all_unpublished_courses(db: Session = Depends(get_db)) -> Dict:
    """
    Fetch all courses that are not published yet.
    """
    courses = db.query(Course).filter(Course.publish_status != PublishStatusEnum.published.value).all()
    if not courses:
        raise HTTPException(status_code=404, detail="No unpublished courses found")

    course_list = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "language": course.language,
            "publish_status": course.publish_status,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
        }
        for course in courses
    ]

    return {"total": len(course_list), "courses": course_list}


# ---------------------- UPDATE COURSE STATUS ----------------------

def update_course_status(db: Session, course_id: int, new_status: PublishStatusEnum) -> dict:
    """
    Update the publication status of a course.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found")

    course.publish_status = new_status.value
    db.commit()
    db.refresh(course)

    return {
        "message": f"Course '{course.title}' status updated to '{course.publish_status}'",
        "course_id": course.id,
        "new_status": course.publish_status
    }


# ---------------------- MENTOR’S COURSES (NO AUTH) ----------------------

def get_courses_by_mentor(db: Session, mentor_id: int) -> Dict:
    """
    Fetch all courses created by a specific mentor (no authentication).
    """
    courses = db.query(Course).filter(Course.created_by_id == mentor_id).all()

    if not courses:
        return {"message": f"No courses found for mentor ID {mentor_id}."}

    course_list = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "language": course.language,
            "publish_status": course.publish_status,
            "created_at": course.created_at,
        }
        for course in courses
    ]

    return {
        "mentor_id": mentor_id,
        "total": len(course_list),
        "courses": course_list
    }
