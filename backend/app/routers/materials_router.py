import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv  # ✅ Add this line

from database import get_db
from Base import Material, MaterialStatusEnum, UserRole
from basemodels import MaterialCreate, MaterialResponse, MaterialUpdate
from app.crud.material_crud import create_material, get_all_materials, delete_material, get_material
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig
from minio import Minio, S3Error
# Router setup
router = APIRouter(prefix="/materials", tags=["Materials"])


load_dotenv()
# ---------------------------
# 🪣 MinIO Configuration
# ---------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_MATERIALS_BUCKET = os.getenv("MINIO_MATERIALS_BUCKET")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

minio_client = Minio(
    MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

MINIO_BASE_URL = MINIO_ENDPOINT  # For building download URLs

# =====================================================
# 📤 UPLOAD MATERIAL TO MINIO (WITH VERSIONING)
# =====================================================
# 🟨 Upload Material to MinIO with Versioning
# =====================================================
@router.post("/upload", response_model=MaterialResponse)
def upload_material(
    file: UploadFile = File(...),
    module_id: int = Form(None),
    lesson_id: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    Uploads a material file to MinIO with versioning enabled.
    If the same file name is uploaded again, MinIO will create a new version.
    """

    # 🪣 Ensure bucket exists and versioning is enabled
    try:
        if not minio_client.bucket_exists(MINIO_MATERIALS_BUCKET):
            minio_client.make_bucket(MINIO_MATERIALS_BUCKET)

        versioning_status = minio_client.get_bucket_versioning(MINIO_MATERIALS_BUCKET)
        if not versioning_status or versioning_status.status != "Enabled":
            minio_client.set_bucket_versioning(
                MINIO_MATERIALS_BUCKET,
                VersioningConfig(status="Enabled")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling versioning: {str(e)}")

    # 📦 Keep same object name to generate new version
    object_name = f"materials/{file.filename}"

    try:
        # Upload to MinIO
        minio_client.put_object(
            bucket_name=MINIO_MATERIALS_BUCKET,
            object_name=object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading to MinIO: {str(e)}")

    # 🌐 File URL
    file_url = f"{MINIO_BASE_URL}/{MINIO_MATERIALS_BUCKET}/{object_name}"

    # 🧾 Create database record
    material_in = MaterialCreate(
        file_name=file.filename,
        file_url=file_url,
        module_id=module_id,
        lesson_id=lesson_id,
        mime_type=file.content_type,
    )
    material = create_material(db, material_in)

    # 🧩 Build response
    response = MaterialResponse.from_orm(material)
    response.preview_url = file_url
    response.message = "✅ Material uploaded with versioning enabled"  # make sure model includes 'message'
    return response


# ----------------- LIST ALL MATERIALS -----------------
@router.get("/list", response_model=list[MaterialResponse])
def list_materials(db: Session = Depends(get_db)):
    """
    Lists all uploaded materials (latest version only).
    """
    materials = get_all_materials(db)
    response = []
    for m in materials:
        r = MaterialResponse.from_orm(m)
        # ✅ Direct MinIO URL for preview/download
        r.preview_url = f"{MINIO_ENDPOINT}/{MINIO_MATERIALS_BUCKET}/{m.file_name}"
        response.append(r)
    return response


# ----------------- UPDATE MATERIAL STATUS -----------------
@router.patch("/{material_id}/status")
def update_material_status(
    material_id: int,
    status: MaterialStatusEnum,
    db: Session = Depends(get_db),
):
    """
    Update the approval status of a material (approved/rejected).
    Only admins should perform this action.
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    material.status = status.value
    db.commit()
    db.refresh(material)

    return {
        "message": f"Material '{material.file_name}' status updated successfully",
        "material_id": material.id,
        "new_status": material.status
    }


# ----------------- DELETE MATERIAL -----------------
# =====================================================
# 🗑️ Delete Material (Database + MinIO)
# =====================================================
@router.delete("/{material_id}")
def delete_material_route(material_id: int, db: Session = Depends(get_db)):
    """
    Deletes a material both from the database and MinIO bucket.
    If versioning is enabled, it deletes only the latest version.
    """

    # 🔍 Fetch the material record
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # 🪣 Extract object name from MinIO URL
    if material.file_url and MINIO_MATERIALS_BUCKET in material.file_url:
        try:
            object_name = material.file_url.split(f"{MINIO_MATERIALS_BUCKET}/", 1)[1]
            minio_client.remove_object(MINIO_MATERIALS_BUCKET, object_name)
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"MinIO deletion failed: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error deleting from MinIO: {str(e)}")

    # 🗑️ Remove from database
    db.delete(material)
    db.commit()

    return {"message": "✅ Material deleted successfully from both database and MinIO"}

# ----------------- DOWNLOAD MATERIAL -----------------
@router.get("/download/{material_id}")
def download_material(material_id: int, db: Session = Depends(get_db)):
    """
    Downloads a material file by its ID.
    """
    material = get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Optional: only approved materials for non-admins
    # if getattr(user, "role", None) != "admin" and material.status != "approved":
    #     raise HTTPException(status_code=403, detail="Material not approved for download")

    if not os.path.exists(material.file_url):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        material.file_url,
        filename=material.file_name,
        media_type=material.mime_type or "application/octet-stream"
    )
