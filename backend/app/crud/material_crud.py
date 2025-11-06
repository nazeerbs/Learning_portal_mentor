from sqlalchemy.orm import Session
from Base import Material,MaterialStatusEnum
from basemodels import MaterialCreate, MaterialUpdate

# ----------------- CREATE MATERIAL -----------------
# =====================================================
# 🟩 Create Material (DB helper)
# =====================================================
def create_material(db: Session, material: MaterialCreate) -> Material:
    new_material = Material(
        file_name=material.file_name,
        file_url=material.file_url,
        mime_type=material.mime_type,
        module_id=material.module_id,
        lesson_id=material.lesson_id,
    )
    db.add(new_material)
    db.commit()
    db.refresh(new_material)  # ✅ Keep inside this function
    return new_material

# ----------------- GET MATERIAL BY ID -----------------
def get_material(db: Session, material_id: int):
    return db.query(Material).filter(Material.id == material_id).first()

# ----------------- GET ALL MATERIALS -----------------
def get_all_materials(db: Session):
    return db.query(Material).all()

# ----------------- UPDATE MATERIAL STATUS -----------------
def update_material_status(db: Session, material_id: int, status: str):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        return None
    material.status = status
    db.commit()
    db.refresh(material)
    return material

# ----------------- DELETE MATERIAL -----------------
import os

def delete_material(db: Session, material_id: int):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        return None
    db.delete(material)
    db.commit()
    return material
