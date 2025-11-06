from fastapi import APIRouter, UploadFile, File, Form, Query, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

# 🧩 Local imports
from database import get_db
from app.crud.lesson_crud import save_lesson_video, get_all_lessons, get_lesson_by_id
from Base import Lesson, LessonSubtitle
from basemodels import SubtitleSchema
from minio import Minio
from dotenv import load_dotenv
from app.crud.translate_crud  import generate_subtitles_background

# 📘 Initialize API router
router = APIRouter()


# =====================================================
# 🟩 Upload Lesson (Create)
# =====================================================
# ---------------- Route ----------------
@router.post("/create/{module_id}")
def upload_lesson_video(
    module_id: int,
    description: str = Form(...),
    file: UploadFile = File(...),
    languages: str = Query("en,hi,fr,es"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Upload new lesson file, save to MinIO & DB, enable versioning, trigger subtitles."""
    result = save_lesson_video(db=db, module_id=module_id, file=file, description=description)

    lesson_id = result["lesson_id"]
    file_url = result["file_url"]
    content_type = result["content_type"]

    if content_type == "video" and background_tasks:
        background_tasks.add_task(
            generate_subtitles_background,
            lesson_id,
            file_url,
            languages
        )
        subtitles_status = "processing"
    else:
        subtitles_status = "skipped"

    return {
        "message": "Lesson uploaded successfully",
        "lesson_id": lesson_id,
        "description": description,
        "content_url": file_url,
        "subtitles_status": subtitles_status
    }



# =====================================================
# 🟨 Update Lesson (Replace File)
# =====================================================
@router.put("/update/{module_id}")
def update_lesson_video(
    module_id: int,
    lesson_id: int = Query(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    languages: str = Query("en,hi"),  # Default translation languages
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Update an existing lesson file and regenerate subtitles if it's a video.
    """
    # ✅ Save updated lesson file (this handles MinIO upload & versioning)
    result = save_lesson_video(
        db=db,
        module_id=module_id,
        file=file,
        lesson_id=lesson_id,
        description=description
    )

    # Extract info from result dict
    lesson_id = result["lesson_id"]
    file_url = result["file_url"]
    content_type = result["content_type"]

    # 🎬 Trigger subtitle regeneration if video
    if content_type == "video" and background_tasks:
        background_tasks.add_task(
            generate_subtitles_background,
            lesson_id,
            file_url,
            languages
        )
        subtitles_status = "processing"
    else:
        subtitles_status = "skipped"

    return {
        "message": "Lesson updated successfully ✅",
        "lesson_id": lesson_id,
        "description": description,
        "content_url": file_url,  # Direct MinIO URL
        "subtitles_status": subtitles_status
    }


# =====================================================
# 🟦 Get All Lessons
# =====================================================
@router.get("/all")
def get_all_lessons_api(db: Session = Depends(get_db)):
    """
    Fetch all lessons available in the database.
    """
    return get_all_lessons(db)


# =====================================================
# 🟪 Get Lesson by ID
# =====================================================
@router.get("/{lesson_id}")
def get_lesson_by_id_api(lesson_id: int, db: Session = Depends(get_db)):
    """
    Fetch a specific lesson by its ID.
    """
    return get_lesson_by_id(lesson_id, db)


# =====================================================
# 🎥 Stream Video
# =====================================================
@router.get("/get-video/{lesson_id}")
def get_video(lesson_id: int, db: Session = Depends(get_db)):
    """
    Stream lesson video file from the uploads folder.
    """
    # 🔍 Find lesson by ID
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson or not lesson.content_url:
        raise HTTPException(status_code=404, detail="Video not found")

    # 🗂️ Normalize path for Windows/Unix systems
    file_path = os.path.normpath(os.path.join("uploads", "lessons", os.path.basename(lesson.content_url)))

    # ⚠️ Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file missing on server")

    # 🎬 Stream video file as response
    return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))


# =====================================================
# 🗣️ Get All Subtitles for a Lesson
# =====================================================
@router.get("/subtitle/{lesson_id}/all")
def get_all_subtitles(lesson_id: int, db: Session = Depends(get_db)):
    """
    Returns all subtitle languages and their file URLs for a given lesson.
    """
    # 🔍 Fetch all subtitle records
    subtitles = db.query(LessonSubtitle).filter(LessonSubtitle.lesson_id == lesson_id).all()
    if not subtitles:
        raise HTTPException(status_code=404, detail="No subtitles found")

    # 📋 Format subtitle info
    result = [
        {
            "id": sub.id,
            "language": sub.language,
            "file_url": f"/api/v1/lessons/subtitle/{lesson_id}/{sub.language}"  # URL to access individual subtitle
        }
        for sub in subtitles
    ]
    return result


# =====================================================
# 📜 Get Subtitle by Language (VTT Format)
# =====================================================
@router.get("/subtitle/{lesson_id}/{language}")
def get_subtitle(lesson_id: int, language: str, db: Session = Depends(get_db)):
    """
    Serve a single subtitle file in VTT format for the specified language.
    """
    # 🔍 Find subtitle by lesson ID and language
    subtitle = (
        db.query(LessonSubtitle)
        .filter(LessonSubtitle.lesson_id == lesson_id)
        .filter(LessonSubtitle.language == language)
        .first()
    )

    # ⚠️ Raise error if not found
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitle not found")

    # 📄 Build VTT content
    vtt_content = f"WEBVTT\n\n{subtitle.subtitle_text}"

    # 📤 Return response as inline VTT file
    return Response(
        content=vtt_content,
        media_type="text/vtt",
        headers={"Content-Disposition": f'inline; filename="subtitle_{lesson_id}_{language}.vtt"'}
    )


# =====================================================
# 🗑️ Delete Lesson
# # =====================================================
# @router.delete("/{lesson_id}")
# def delete_lesson_api(lesson_id: int, db: Session = Depends(get_db)):
#     """
#     Delete a lesson record from the database.
#     """
#     # 🔍 Check if lesson exists
#     lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
#     if not lesson:
#         raise HTTPException(status_code=404, detail="Lesson not found")

#     # ❌ Delete from database
#     db.delete(lesson)
#     db.commit()

#     return {"message": f"Lesson {lesson_id} deleted successfully"}


@router.delete("/{lesson_id}")
def delete_lesson_api(lesson_id: int, db: Session = Depends(get_db)):
    """
    Delete a lesson record and its file from MinIO.
    """

    # ✅ Load environment variables dynamically
    load_dotenv()
    MINIO_URL = os.getenv("MINIO_URL")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET = os.getenv("MINIO_COURSES_BUCKET")

    # ✅ Check if lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ✅ Extract the MinIO object name from the stored content URL
    file_url = lesson.content_url
    object_name = None
    if file_url and f"{MINIO_BUCKET}/" in file_url:
        object_name = file_url.split(f"{MINIO_BUCKET}/")[-1]

    # ✅ Initialize MinIO client
    client = Minio(
        MINIO_URL.replace("http://", "").replace("https://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_URL.startswith("https")
    )

    # ✅ Delete file from MinIO if found
    if object_name:
        try:
            client.remove_object(MINIO_BUCKET, object_name)
            print(f"🗑️ Deleted file '{object_name}' from MinIO bucket '{MINIO_BUCKET}'")
        except Exception as e:
            print(f"⚠️ Failed to delete file from MinIO: {e}")

    # ✅ Delete lesson record from database
    db.delete(lesson)
    db.commit()

    return {"message": f"Lesson {lesson_id} and its file deleted successfully"}

# =====================================================
# 🟦 Get Lessons by Module ID
# =====================================================
@router.get("/")
def get_lessons_by_module(module_id: int, db: Session = Depends(get_db)):
    """
    Fetch all lessons belonging to a specific module.
    """
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).all()
    if not lessons:
        raise HTTPException(status_code=404, detail="No lessons found for this module")

    return [
        {
            "id": lesson.id,
            "description": lesson.description,
            "content_url": lesson.content_url,
            "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
        }
        for lesson in lessons
    ]
