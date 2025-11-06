from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from app.crud.modules_crud import create_module, get_module, list_modules_by_course, update_module, delete_module
from basemodels import ModuleCreate, ModuleUpdate, ModuleSchema

# 🔹 Use plural "modules" to match frontend
router = APIRouter()

# ✅ Create module under a course
@router.post("/create", response_model=ModuleSchema)
def router_create_module(module_data: ModuleCreate, db: Session = Depends(get_db)):
    """
    Create a new module.
    module_data must include course_id, title, optional description, position
    """
    module = create_module(
        db,
        course_id=module_data.course_id,
        title=module_data.title,
        description=module_data.description,
        position=module_data.position
    )
    return module

# ✅ Get all modules for a specific course
@router.get("/", response_model=List[ModuleSchema])
def router_list_modules(course_id: int = Query(...), db: Session = Depends(get_db)):
    """
    List all modules for a given course_id
    """
    modules = list_modules_by_course(db, course_id)
    return modules

# ✅ Get single module by ID
@router.get("/{module_id}", response_model=ModuleSchema)
def router_get_module(module_id: int, db: Session = Depends(get_db)):
    module = get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

# ✅ Update module
@router.put("/{module_id}", response_model=ModuleSchema)
def router_update_module(module_id: int, module_data: ModuleUpdate, db: Session = Depends(get_db)):
    module = get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    updated_module = update_module(
        db,
        module,
        title=module_data.title,
        description=module_data.description,
        position=module_data.position
    )
    return updated_module

# ✅ Delete module
@router.delete("/{module_id}")
def router_delete_module(module_id: int, db: Session = Depends(get_db)):
    module = get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    delete_module(db, module)
    return {"detail": "Module deleted successfully"}
