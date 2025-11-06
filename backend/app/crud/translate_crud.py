import os
from datetime import datetime
import asyncio
import whisper
from io import BytesIO
from Base import Lesson, LessonSubtitle
from basemodels import SubtitleSchema
from database import SessionLocal
import requests
from dotenv import load_dotenv
from minio import Minio
import tempfile


# Get the translation API URL from environment variables
API_URL = os.getenv("API_URL")


# -----------------------------
# File Type Mapping
# -----------------------------
EXTENSION_MAP = {
    "mp4": "video", "mov": "video", "avi": "video", "mkv": "video",
    "pdf": "document", "doc": "document", "docx": "document", "txt": "text",
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image"
}


def segments_to_vtt(segments: list) -> str:
    vtt = "WEBVTT\n\n"
    for seg in segments:
        start_h = int(seg['start'] // 3600)
        start_m = int((seg['start'] % 3600) // 60)
        start_s = int(seg['start'] % 60)
        end_h = int(seg['end'] // 3600)
        end_m = int((seg['end'] % 3600) // 60)
        end_s = int(seg['end'] % 60)

        start_ms = int((seg['start'] % 1) * 1000)
        end_ms = int((seg['end'] % 1) * 1000)

        vtt += f"{start_h:02}:{start_m:02}:{start_s:02}.{start_ms:03} --> {end_h:02}:{end_m:02}:{end_s:02}.{end_ms:03}\n"
        vtt += seg['text'].strip() + "\n\n"
    return vtt

def generate_subtitles_background(lesson_id: int, file_path: str, languages: str):
    """
    Generate subtitles for a given lesson video stored in MinIO or local path.
    Downloads the file to a local folder and deletes it after use.
    """
    load_dotenv()  # ✅ Load environment variables

    # ✅ MinIO Configuration
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET = os.getenv("MINIO_COURSES_BUCKET")

    # ✅ Local working folder for subtitle generation
    temp_dir = os.path.join(os.getcwd(), "subtitles_temp")
    os.makedirs(temp_dir, exist_ok=True)

    db = SessionLocal()
    local_video_path = None
    try:
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            print(f"❌ Lesson {lesson_id} not found for subtitle generation.")
            return

        print(f"🎬 Generating subtitles for lesson {lesson.id} ...")

        # ✅ If the video is in MinIO, download it
        if file_path.startswith("http://") or file_path.startswith("https://"):
            client = Minio(
                MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_ENDPOINT.startswith("https")
            )

            # Extract file name from URL
            object_name = file_path.split(f"{MINIO_BUCKET}/")[-1]
            filename = os.path.basename(object_name)
            local_video_path = os.path.join(temp_dir, filename)

            # 🧩 Download file to local folder
            client.fget_object(MINIO_BUCKET, object_name, local_video_path)
        else:
            # If it’s already local
            local_video_path = file_path

        # ✅ Transcribe video using Whisper
        model = whisper.load_model("base")
        result = model.transcribe(local_video_path, language="en")
        segments = result.get("segments", [])

        target_languages = [lang.strip() for lang in languages.split(",")]

        for lang in target_languages:
            if lang == "en":
                vtt_text = segments_to_vtt(segments)
            else:
                translated_segments = []
                for seg in segments:
                    translated_text = translate_text(seg['text'], target_lang=lang)
                    translated_segments.append({
                        "start": seg['start'],
                        "end": seg['end'],
                        "text": translated_text
                    })
                vtt_text = segments_to_vtt(translated_segments)

            subtitle = LessonSubtitle(
                lesson_id=lesson.id,
                subtitle_text=vtt_text,
                language=lang,
                created_at=datetime.utcnow()
            )
            db.add(subtitle)

        db.commit()
        print(f"✅ Subtitles generated for lesson {lesson.id} in {languages}")

    except Exception as e:
        print(f"❌ Subtitle generation failed for lesson {lesson_id}: {e}")

    finally:
        # 🧹 Clean up downloaded video after transcription
        if local_video_path and os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
                print(f"🧹 Deleted temp file: {local_video_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup failed: {cleanup_error}")
        db.close()





def translate_text(text: str, target_lang: str):
    """Translate a given English text into the target language."""
    
    # Return empty if no text is provided
    if not text:
        return ""
    
    try:
        # Send POST request to the translation API
        response = requests.post(API_URL, data={
            "q": text,          # Text to translate
            "source": "en",     # Source language
            "target": target_lang,  # Target language (e.g., hi, fr)
            "format": "text"    # Type of content
        })
        
        # Raise error if response status is not OK
        response.raise_for_status()
        
        # Return translated text from API response
        return response.json().get("translatedText", "")
    
    except Exception as e:
        # Print error for debugging if translation fails
        print(f"Translation failed for '{target_lang}': {e}")
        return ""
