from fastapi import APIRouter, Response, UploadFile, File, Depends, HTTPException, Query
import subprocess
import whisper
import os
from datetime import datetime
from fastapi import BackgroundTasks
from typing import Text
from Base import Module, Lesson
from sqlalchemy.orm import Session, joinedload
from database import get_db
from basemodels import SubtitleSchema
from minio import Minio
from dotenv import load_dotenv
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig

# ✅ Load environment variables
load_dotenv()

# ✅ Mapping of file extensions to content types
EXTENSION_MAP = {
    "mp4": "video",
    "mov": "video",
    "avi": "video",
    "mkv": "video",
    "pdf": "document",
    "doc": "document",
    "docx": "document",
    "txt": "text",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "gif": "image"
}

# ✅ Load MinIO configuration dynamically from environment
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_COURSES_BUCKET")
MINIO_BASE_URL = os.getenv("MINIO_BASE_URL", f"http://{MINIO_ENDPOINT}")

# ✅ Initialize MinIO client dynamically
minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL
)

# ---------------- Function ----------------
def save_lesson_video(
    db: Session,
    module_id: int,
    file: UploadFile,
    lesson_id: int = None,
    description: str = None
):
    """
    Save uploaded lesson file to MinIO and create or update a Lesson.
    Versioning is used if the file already exists (same key).
    """

    # 🔍 Check module exists
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # 🧩 Detect file type
    ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    content_type = EXTENSION_MAP.get(ext, "other")

    # 🪣 Ensure bucket exists and enable versioning
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)

        versioning_status = minio_client.get_bucket_versioning(MINIO_BUCKET_NAME)
        if not versioning_status or versioning_status.status != "Enabled":
            minio_client.set_bucket_versioning(
                MINIO_BUCKET_NAME,
                VersioningConfig(status="Enabled")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling versioning: {str(e)}")

    # ✏️ Check if lesson already exists
    existing_lesson = None
    if lesson_id:
        existing_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    # 🕒 Keep same object name if updating (so versioning works)
    if existing_lesson and existing_lesson.content_url:
        object_name = existing_lesson.content_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"lessons/{timestamp}_{file.filename}"

    # 📤 Upload file (creates a *new version* if same name)
    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading to MinIO: {str(e)}")

    # 🌐 Generate MinIO file URL
    file_url = f"{MINIO_BASE_URL}/{MINIO_BUCKET_NAME}/{object_name}"

    # 🧾 Update or create lesson record
    if existing_lesson:
        existing_lesson.content_url = file_url
        existing_lesson.content_type = content_type
        existing_lesson.description = description or existing_lesson.description
        existing_lesson.updated_at = datetime.utcnow()
        lesson = existing_lesson
    else:
        lesson = Lesson(
            module_id=module_id,
            title=os.path.splitext(file.filename)[0],
            content_type=content_type,
            content_url=file_url,
            description=description,
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(lesson)

    db.commit()
    db.refresh(lesson)

    return {
        "lesson_id": lesson.id,
        "file_url": file_url,
        "content_type": content_type,
        "message": "✅ Lesson uploaded with versioning enabled"
    }

# ------------------------------------------------------
# Delete Lesson and Its Associated File
# ------------------------------------------------------
def delete_lesson(lesson_id: int, db: Session):
    """
    Delete a lesson by ID and remove associated file if exists.
    """
    # 🔍 Find lesson by ID
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise Exception(f"Lesson with ID {lesson_id} not found")

    # 🗑️ Delete the lesson file from disk if it exists
    if lesson.content_url:
        file_path = lesson.content_url.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

    # ❌ Delete lesson record from DB
    db.delete(lesson)
    db.commit()

    return {"message": f"Lesson with ID {lesson_id} deleted successfully"}


# ------------------------------------------------------
# Fetch All Lessons (with Subtitles)
# ------------------------------------------------------
def get_all_lessons(db: Session):
    """
    Retrieve all lessons with related files and subtitles.
    """
    # 📥 Query lessons and preload subtitles
    lessons = db.query(Lesson).options(
        # joinedload(Lesson.files),  # optional: if you have files table
        joinedload(Lesson.subtitles)
    ).all()

    # ⚠️ Handle no data case
    if not lessons:
        raise HTTPException(status_code=404, detail="No lessons found")

    result = []

    # 🧾 Format output data
    for lesson in lessons:
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "content_type": lesson.content_type,
            "content_url": lesson.content_url,
            "language": lesson.language,
            "module_id": lesson.module_id,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at
        })

    return result


# ------------------------------------------------------
# Fetch Lesson by ID (with Subtitles)
# ------------------------------------------------------
def get_lesson_by_id(lesson_id: int, db: Session):
    """
    Retrieve a single lesson by ID with related files and subtitles.
    """
    # 🔍 Query specific lesson with subtitles
    lesson = db.query(Lesson).options(
        # joinedload(Lesson.files),
        joinedload(Lesson.subtitles)
    ).filter(Lesson.id == lesson_id).first()

    # ⚠️ If not found, raise HTTP error
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson with ID {lesson_id} not found")

    # 🧾 Return lesson data
    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "content_type": lesson.content_type,
        "content_url": lesson.content_url,
        "language": lesson.language,
        "module_id": lesson.module_id,
        "created_at": lesson.created_at,
        "updated_at": lesson.updated_at
    }
