# crud.py
from sqlalchemy.orm import Session
import Base, basemodels
from app.crud.auth import hash_password,verify_password
from fastapi import HTTPException


from sqlalchemy.orm import Session
from Base import User, UserRole

from basemodels import UserCreate

def create_user(db: Session, user_in):
    # ✅ Normalize role input (case-insensitive)
    role_value = user_in.role.strip().lower()

    # ✅ Validate role
    if role_value not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {user_in.role}. Must be one of {[r.value for r in UserRole]}"
        )

    # ✅ Check if email already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    # ✅ Create new user
    new_user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=UserRole(role_value),
        hashed_password=hash_password(user_in.password),
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str):
    # ✅ Query using the actual User model (not Base.User)
    user = db.query(User).filter(User.email == email).first()

    # 🔒 Check if user exists and has a password
    if not user or not user.hashed_password:
        return None

    # ✅ Verify password using your hashing function
    if not verify_password(password, user.hashed_password):
        return None

    return user


def assign_mentor(db: Session, mentor_id: int, course_id=None, group_id=None, learner_id=None):
    # avoid duplicates; UniqueConstraint handles DB-level check
    existing = db.query(Base.MentorAssignment).filter_by(
        mentor_id=mentor_id, course_id=course_id, group_id=group_id, learner_id=learner_id
    ).first()
    if existing:
        return existing
    ma = Base.MentorAssignment(mentor_id=mentor_id, course_id=course_id, group_id=group_id, learner_id=learner_id)
    db.add(ma); db.commit(); db.refresh(ma)
    return ma

def unassign_mentor(db: Session, assignment_id: int):
    asg = db.query(Base.MentorAssignment).get(assignment_id)
    if not asg:
        return None
    db.delete(asg); db.commit()
    return True