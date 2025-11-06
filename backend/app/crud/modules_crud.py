from sqlalchemy.orm import Session
from typing import Optional
from Base import Course, Module
from fastapi import HTTPException


# ---------- Modules ----------
def create_module(db: Session, course_id: int, title: str, description: str = None, position: int = 0) -> Module:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    module = Module(course_id=course_id, title=title, description=description, position=position)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module  # Return the SQLAlchemy object itself

def get_module(db: Session, module_id: int) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

def list_modules_by_course(db: Session, course_id: int):
    return db.query(Module).filter(Module.course_id == course_id).all()

def update_module(db: Session, module: Module, title: str = None, description: str = None, position: int = None) -> Module:
    if title is not None:
        module.title = title
    if description is not None:
        module.description = description
    if position is not None:
        module.position = position
    db.commit()
    db.refresh(module)
    return module

def delete_module(db: Session, module: Module):
    db.delete(module)
    db.commit()