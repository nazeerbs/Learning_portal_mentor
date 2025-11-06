# main.py
from fastapi import FastAPI, Depends, HTTPException,APIRouter
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from app.crud.Analytics_crud import (
    update_engagement,update_progress,fetch_learner_progress,fetch_course_report,log_mentor_interaction)
from basemodels import (
    LearnerProgressBase, LearnerEngagementBase, MentorInteractionBase, CourseBase, ResponseMessage
)
from datetime import datetime, timedelta
from Base import User,LearnerEngagement,LearnerProgress,Course

router = APIRouter()

# Learners
# @router.post("/learners", response_model=ResponseMessage)
# def add_learner(name: str, email: str, db: Session = Depends(get_db)):
#     learner = create_learner(db, name, email)
#     return {"message": f"Learner {learner.name} added successfully."}

# Courses
# @app.post("/courses", response_model=ResponseMessage)
# def add_course(course: CourseBase, db: Session = Depends(get_db)):
#     c = Base.create_course(db, course)
#     return {"message": f"Course '{c.title}' added successfully."}

# @app.put("/courses/{course_id}", response_model=ResponseMessage)
# def edit_course(course_id: int, course: CourseBase, db: Session = Depends(get_db)):
#     updated = Base.update_course(db, course_id, course)
#     if not updated:
#         raise HTTPException(status_code=404, detail="Course not found")
#     return {"message": f"Course '{updated.title}' updated successfully."}

# Progress
# =========================================================
# 📊 Progress APIs
# =========================================================
@router.post("/progress", response_model=ResponseMessage)
def add_or_update_progress(progress: LearnerProgressBase, db: Session = Depends(get_db)):
    updated = update_progress(db, progress)
    return {"message": f"Progress updated to {updated.progress_percent}%."}


@router.get("/progress/{learner_id}")
def get_learner_progress(learner_id: int, db: Session = Depends(get_db)):
    return fetch_learner_progress(db, learner_id)


@router.get("/course-report/{course_id}")
def get_course_report(course_id: int, db: Session = Depends(get_db)):
    return fetch_course_report(db, course_id)


# =========================================================
# 🕒 Engagement API
# =========================================================
@router.put("/engagement", response_model=ResponseMessage)
def update_learner_engagement(engagement: LearnerEngagementBase, db: Session = Depends(get_db)):
    updated = update_engagement(db, engagement)
    return {"message": "Learner engagement updated successfully."}


# =========================================================
# 🧑‍🏫 Mentor Logs
@router.post("/mentor-log", response_model=ResponseMessage)
def mentor_interaction_log(log: MentorInteractionBase, db: Session = Depends(get_db)):
    entry = log_mentor_interaction(db, log)
    return {"message": f"Mentor interaction logged with ID {entry.id}."}


# =========================================================
# 👩‍🎓 Student Analytics (Progress + Engagement)
# =========================================================
@router.get("/students")
def get_students(db: Session = Depends(get_db)):
    learners = db.query(User).filter(User.role == "student").all()
    result = []

    for learner in learners:
        # --- Progress ---
        progress_record = (
            db.query(LearnerProgress)
            .filter(LearnerProgress.learner_id == learner.id)
            .first()
        )
        progress = progress_record.progress_percent if progress_record else 0.0

        # --- Engagement ---
        engagement_record = (
            db.query(LearnerEngagement)
            .filter(LearnerEngagement.learner_id == learner.id)
            .first()
        )

        last_active_at = None
        if engagement_record:
            if hasattr(engagement_record, "last_login"):
                last_active_at = engagement_record.last_login
            elif hasattr(engagement_record, "last_active"):
                last_active_at = engagement_record.last_active
            elif hasattr(engagement_record, "last_seen"):
                last_active_at = engagement_record.last_seen

        # --- Active/Inactive/Risk Status ---
        now = datetime.utcnow()
        active_status = (
            "Active"
            if last_active_at and last_active_at > now - timedelta(days=14)
            else "Inactive"
        )
        risk_status = "At Risk" if progress < 50 else active_status

        # --- Full Name ---
        full_name = f"{learner.first_name} {learner.last_name or ''}".strip()

        # # --- Mocked task data (optional for UI) ---
        # total_tasks = 30
        # tasks_completed = round((progress / 100) * total_tasks)

        result.append({
            "id": learner.id,
            "name": full_name,
            "email": learner.email,
            "progress": progress,
            "status": risk_status,  # Must exactly match "At Risk" etc.
            "lastActive": (
                last_active_at.strftime("%b %d, %Y")
                if last_active_at else "N/A"
            ),
            # "tasksCompleted": tasks_completed,
            # "totalTasks": total_tasks,
        })

    return result
@router.get("/courses")
def get_courses_analytics(db: Session = Depends(get_db)):
    """
    Fetch analytics summary for all courses:
    - Total students
    - Average progress
    - Course status (Published/Unpublished/At Risk)
    - Activity breakdown (Completed/In Progress/Not Started)
    """
    courses = db.query(Course).all()
    result = []

    for course in courses:
        progress_records = (
            db.query(LearnerProgress)
            .filter(LearnerProgress.course_id == course.id)
            .all()
        )

        total_learners = len(progress_records)

        avg_progress = (
            round(sum([p.progress_percent for p in progress_records]) / total_learners, 2)
            if total_learners > 0 else 0.0
        )

        # Determine course status
        status = (
            "Published"
            if str(course.publish_status).lower() == "published"
            else "Unpublished"
        )
        risk_status = "At Risk" if avg_progress < 50 else status

        # 🟢 Learner activity breakdown
        completed = len([p for p in progress_records if p.progress_percent >= 90])
        in_progress = len([p for p in progress_records if 0 < p.progress_percent < 90])
        not_started = total_learners - (completed + in_progress)

        activity_data = [
            {"name": "Completed", "value": completed},
            {"name": "In Progress", "value": in_progress},
            {"name": "Not Started", "value": not_started},
        ]

        result.append({
            "title": course.title,
            "description": course.description or "",
            "createdAt": course.created_at.strftime("%b %d, %Y") if course.created_at else "N/A",
            "stats": {
                "totalStudents": total_learners,
                "avgProgress": avg_progress,
                "status": risk_status
            },
            "activity": activity_data
        })

    return result
# from app.crud.auth import verify_password,create_access_token

# from basemodels import LoginRequest
# @router.post("/login")
# def login_user(user_in: LoginRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == user_in.email).first()
#     if not user or not verify_password(user_in.password, user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = create_access_token(subject=user.id, role=user.role, email=user.email)
#     return {"access_token": token, "token_type": "bearer"}

