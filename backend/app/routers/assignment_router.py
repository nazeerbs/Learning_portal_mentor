from fastapi import APIRouter, UploadFile, Form, Depends, File
from sqlalchemy.orm import Session
from database import get_db
from app.crud.assignment_crud import upload_assignment_file
from basemodels import AssignmentSchema

router = APIRouter(prefix="/assignments", tags=["Assignments"])
@router.post("/upload", response_model=AssignmentSchema)
def upload_assignment(
    course_id: int = Form(...),
    module_id: int = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return upload_assignment_file(db, course_id, module_id, file, title, description)