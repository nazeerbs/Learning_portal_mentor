from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from Base import Certification, User

from fastapi.responses import FileResponse, RedirectResponse
import os
from dotenv import load_dotenv
from minio import Minio

load_dotenv()

router = APIRouter()

# ------------------------------------------------------------
# 🌐 MinIO Configuration
# ------------------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_CERT_BUCKET = os.getenv("MINIO_CERT_BUCKET")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL
)

# ------------------------------------------------------------
# 📄 1️⃣ Get All Certificates (Admin Panel)
# ------------------------------------------------------------
@router.get("/all")
def get_all_certificates(db: Session = Depends(get_db)):
    """
    Returns a list of all issued certificates.
    """
    certs = db.query(Certification).all()
    if not certs:
        raise HTTPException(status_code=404, detail="No certificates found")
    
    return [
        {
            "id": c.id,
            "student_id": c.student_id,
            "certificate_status": c.certificate_status,
            "issue_date": c.issue_date,
            "file_url": c.file_url,
        }
        for c in certs
    ]


# ------------------------------------------------------------
# 👤 2️⃣ Get Certificate for a Specific Student
# ------------------------------------------------------------
# ------------------------------------------------------------
# 👤 Get Certificate for a Specific Student
# ------------------------------------------------------------
# ✅ Use the correct bucket name that contains the certificates


@router.get("/student/{student_id}")
def get_student_certificate(student_id: int, db: Session = Depends(get_db)):
    cert = db.query(Certification).filter(Certification.student_id == student_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found for this student")

    if not cert.file_url:
        raise HTTPException(status_code=404, detail="Certificate file URL not available")

    # ✅ Extract the object key based on correct bucket
    object_key = cert.file_url.replace(f"http://{MINIO_ENDPOINT}/{MINIO_CERT_BUCKET}/", "")

    try:
        minio_client.stat_object(MINIO_CERT_BUCKET, object_key)
    except Exception:
        raise HTTPException(status_code=404, detail="Certificate file missing in MinIO")

    return {
        "student_id": cert.student_id,
        "certificate_status": cert.certificate_status,
        "issue_date": cert.issue_date,
        "file_url": cert.file_url,
    }

# ------------------------------------------------------------
# 🔗 3️⃣ Redirect to MinIO Public URL (Preview)
# ------------------------------------------------------------
@router.get("/preview/{student_id}")
def preview_certificate(student_id: int, db: Session = Depends(get_db)):
    """
    Redirect user to view certificate directly from MinIO (public URL).
    """
    cert = db.query(Certification).filter(Certification.student_id == student_id).first()
    if not cert or not cert.file_url:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return RedirectResponse(url=cert.file_url)


# ------------------------------------------------------------
# 💾 4️⃣ Download Certificate from MinIO
# ------------------------------------------------------------
# =====================================================
# 📥 DOWNLOAD CERTIFICATE FOR END USER
# # =====================================================
# @router.get("/download/{student_id}")
# def download_certificate(student_id: int, db: Session = Depends(get_db)):
#     """
#     Allows end users to download their certificate as a PDF file.
#     """
#     # 🔍 Fetch certificate record from DB
#     cert = db.query(Certification).filter(Certification.student_id == student_id).first()
#     if not cert or not cert.file_url:
#         raise HTTPException(status_code=404, detail="Certificate not found")

#     # 🧩 Extract object path from file_url
#     # Example URL: http://127.0.0.1:9000/course-certificates/certificates/certificate_user_1.pdf
#     object_name = cert.file_url.split(f"{MINIO_CERT_BUCKET}/")[-1]

#     # 🕒 Create temporary local file path
#     file_name = object_name.split("/")[-1]
#     local_path = f"temp_{file_name}"

#     try:
#         # 📥 Download from MinIO to temp file
#         minio_client.fget_object(
#             MINIO_CERT_BUCKET,
#             object_name,
#             local_path
#         )

#         # 📤 Return file to user (triggers browser download)
#         return FileResponse(
#             path=local_path,
#             media_type="application/pdf",
#             filename=file_name
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error downloading certificate: {str(e)}")

#     finally:
#         # 🧹 Remove temp file after sending
#         if os.path.exists(local_path):
#             try:
#                 os.remove(local_path)
#             except:
#                 pass
