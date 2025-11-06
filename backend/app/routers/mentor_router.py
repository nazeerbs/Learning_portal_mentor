from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud.mentor_crud import get_courses_by_mentor, get_all_mentors, assign_student_to_mentor, get_students_by_mentor
import basemodels
from database import get_db

router = APIRouter()

# Get all mentors
@router.get("/", response_model=list[basemodels.UserResponse])
def fetch_all_mentors(db: Session = Depends(get_db)):
    mentors = get_all_mentors(db)
    if not mentors:
        raise HTTPException(status_code=404, detail="No mentors found")
    return mentors

# Get courses assigned to a mentor
@router.get("/{mentor_id}/courses", response_model=basemodels.MentorCoursesResponse)
def fetch_courses_by_mentor(mentor_id: int, db: Session = Depends(get_db)):
    result = get_courses_by_mentor(db, mentor_id)
    if not result:
        raise HTTPException(status_code=404, detail="No courses found for this mentor")
    return result
# Assign student to mentor
@router.post("/{mentor_id}/assign-student/{student_id}")
def assign_student(mentor_id: int, student_id: int, db: Session = Depends(get_db)):
    mentor = assign_student_to_mentor(db, mentor_id, student_id)
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor or Student not found")
    return {"message": f"Student {student_id} assigned to mentor {mentor_id}"}

# Get all students under a mentor
@router.get("/{mentor_id}/students")
def fetch_students_by_mentor(mentor_id: int, db: Session = Depends(get_db)):
    result = get_students_by_mentor(db, mentor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Mentor not found or has no students")
    return result