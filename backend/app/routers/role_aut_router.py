# main.py
from fastapi import FastAPI, Depends, HTTPException, status,APIRouter,Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, Base, engine
import Base, basemodels
from app.crud.role_auth_crud import (create_user, authenticate_user,unassign_mentor,assign_mentor)
from app.crud.auth import create_access_token, get_current_user, require_role, verify_password
from app.crud.auth import hash_password, verify_password  # small helpers
from dotenv import load_dotenv
import os
from Base import User,UserRole
from typing import List
from basemodels import UserOut

load_dotenv()


router = APIRouter()
# ----- Auth endpoints (local) -----
@router.post("/register", response_model=basemodels.UserOut)
def register(user_in: basemodels.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(db, user_in)

    return basemodels.UserOut(
    id=user.id,
    first_name=user.first_name,
    last_name=user.last_name,
    email=user.email,
    role=user.role.value if hasattr(user.role, "value") else str(user.role),
    is_active=user.is_active
)   

@router.post("/token", response_model=basemodels.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(subject=str(user.id), role=user.role.name, email=user.email)
    return {"access_token": token, "token_type": "bearer"}

# ----- current user -----
@router.get("/me", response_model=basemodels.UserOut)
def read_me(current_user: basemodels.UserOut = Depends(get_current_user)):
    return current_user
# ----- Admin helper endpoints -----
# @router.post("/roles", dependencies=[Depends(require_role("admin"))])
# def create_role(r: basemodels.RoleCreate, db: Session = Depends(get_db)):
#     role = create_role_if_not_exists(db, r.name)
#     return {"name": role.name, "id": role.id}

# @router.post("/courses", dependencies=[Depends(require_role("admin", "mentor"))], response_model=basemodels.CourseOut)
# def create_course(c: basemodels.CourseCreate, db: Session = Depends(get_db)):
#     course = crud.create_course(db, c.title, c.description)
#     return course

@router.get("/mentors", response_model=List[UserOut])
def list_mentors(db: Session = Depends(get_db)):
    mentors = db.query(Base.User).filter(Base.User.role == UserRole.mentor).all()

    # ✅ Convert ORM objects to dicts matching UserOut
    result = [
        UserOut(
        id=m.id,
        email=m.email,
        first_name=m.first_name or "",
        last_name=m.last_name or "",
        role=m.role.name if hasattr(m.role, "name") else str(m.role),
        is_active=m.is_active
)
        for m in mentors
    ]
    return result

@router.post(
    "/mentors/assign",
    dependencies=[Depends(require_role("admin", "mentor"))],
    response_model=basemodels.AssignmentOut
)
@router.post(
    "/mentors/assign",
    dependencies=[Depends(require_role("admin", "mentor"))],
    response_model=basemodels.AssignmentOut
)
def assign_mentor_api(
    a: basemodels.AssignmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ If mentor is assigning, they can only assign themselves
    if current_user.role == "mentor" and current_user.id != a.mentor_id:
        raise HTTPException(status_code=403, detail="Mentors can only assign themselves")

    # ✅ call actual CRUD function (not this same route)
    ma = assign_mentor(
        db,
        mentor_id=a.mentor_id,
        course_id=a.course_id,
        group_id=a.group_id,
        learner_id=a.learner_id
    )

    return basemodels.AssignmentOut(
        id=ma.id,
        mentor_id=ma.mentor_id,
        course_id=ma.course_id,
        group_id=ma.group_id,
        learner_id=ma.learner_id
    )

@router.post("/mentors/unassign", dependencies=[Depends(require_role("admin", "mentor"))])
def unassign(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment_id = payload.get("assignment_id")
    if assignment_id is None:
        raise HTTPException(status_code=400, detail="assignment_id required")
    success = unassign_mentor(db, assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"ok": True}

@router.get("/mentors/assignments", dependencies=[Depends(require_role("admin", "mentor"))])
def list_assignments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # mentors see only their assignments
    query = db.query(Base.MentorAssignment)
    
    # ✅ Fix: Compare role directly as string
    if current_user.role == "mentor":
        query = query.filter(Base.MentorAssignment.mentor_id == current_user.id)

    rows = query.all()
    
    return [
        basemodels.AssignmentOut(
            id=r.id,
            mentor_id=r.mentor_id,
            course_id=r.course_id,
            group_id=r.group_id,
            learner_id=r.learner_id
        )
        for r in rows
    ]
@router.get("/users")
def list_users_by_role(
    role: str = Query(..., description="Role to filter by (student, mentor, admin)"),
    db: Session = Depends(get_db)
):
    # Normalize and validate role
    role_lower = role.lower()
    if role_lower not in UserRole.__members__:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Must be one of {list(UserRole.__members__.keys())}"
        )

    role_enum = UserRole[role_lower]

    # Fetch users with the given role
    users = db.query(Base.User).filter(Base.User.role == role_enum).all()

    if not users:
        raise HTTPException(status_code=404, detail=f"No users found with role '{role}'")

    return users


