import os
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from minio import Minio
from dotenv import load_dotenv
from Base import Assignment

load_dotenv()

# -------------------------------
# ✅ MinIO Configuration
# -------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = os.getenv("MINIO_ASSIGNMENT_BUCKET", "course-assignments")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

# -------------------------------
# ✅ MinIO Client Setup
# -------------------------------
minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL
)


# ==========================================================
# 📤 Upload Assignment File (CRUD)
# ==========================================================
def upload_assignment_file(
    db: Session,
    course_id: int,
    module_id: int,
    file: UploadFile,
    title: str,
    description: str
):
    """
    Uploads an assignment file to MinIO and creates an Assignment record in DB.
    """
    # 🪣 Ensure bucket exists
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO bucket error: {str(e)}")

    # 🕒 Unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = file.filename.replace(" ", "_")  # remove spaces
    filename = f"{timestamp}_{safe_filename}"
    object_name = f"assignments/{filename}"

    # 📤 Upload file to MinIO
    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=-1,  # unknown length for streaming upload
            part_size=10 * 1024 * 1024,  # 10 MB chunks
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # 🌐 Construct accessible file URL
    file_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"

    # 💾 Save record in DB
    try:
        assignment = Assignment(
            title=title,
            description=description,
            file_url=file_url,
            course_id=course_id,
            module_id=module_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return assignment
