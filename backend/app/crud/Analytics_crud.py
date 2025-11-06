# methods.py
from sqlalchemy.orm import Session
from Base import  Course, LearnerProgress, LearnerEngagement, MentorInteractionLog,User
from basemodels import LearnerProgressBase, LearnerEngagementBase, MentorInteractionBase, CourseBase
from fastapi import HTTPException
from datetime import datetime, timezone


# # Learner CRUD
# def create_learner(db: Session, name: str, email: str):
#     learner = Learner(name=name, email=email)
#     db.add(learner)
#     db.commit()
#     db.refresh(learner)
#     return learner

# # Course CRUD
# def create_course(db: Session, course_data: CourseBase):
#     course = Course(**course_data.dict())
#     db.add(course)
#     db.commit()
#     db.refresh(course)
#     return course

# def update_course(db: Session, course_id: int, course_data: CourseBase):
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         return None
#     course.title = course_data.title
#     course.batch = course_data.batch
#     db.commit()
#     db.refresh(course)
#     return course
# =========================================================
# 📊 Progress CRUD
# =========================================================
def update_progress(db: Session, progress_data: LearnerProgressBase):
    """Add or update learner progress for a course."""
    progress = (
        db.query(LearnerProgress)
        .filter(
            LearnerProgress.learner_id == progress_data.learner_id,
            LearnerProgress.course_id == progress_data.course_id,
        )
        .first()
    )

    if progress:
        progress.progress_percent = progress_data.progress_percent
        progress.updated_at = datetime.utcnow()
    else:
        progress = LearnerProgress(**progress_data.model_dump())
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress


def fetch_learner_progress(db: Session, learner_id: int):
    """Fetch progress records for a specific learner."""
    progress_list = (
        db.query(LearnerProgress)
        .filter(LearnerProgress.learner_id == learner_id)
        .all()
    )
    if not progress_list:
        raise HTTPException(status_code=404, detail="No progress records found for this learner.")
    return progress_list


def fetch_course_report(db: Session, course_id: int):
    """Fetch progress report for all learners in a course."""
    progress_list = (
        db.query(LearnerProgress)
        .filter(LearnerProgress.course_id == course_id)
        .all()
    )
    if not progress_list:
        raise HTTPException(status_code=404, detail="No learners found for this course.")
    return progress_list


# =========================================================
# 🕒 Engagement CRUD
# =========================================================
def update_engagement(db: Session, engagement_data: LearnerEngagementBase):
    """Update or insert learner engagement (session time & last login)."""
    engagement = (
        db.query(LearnerEngagement)
        .filter(LearnerEngagement.learner_id == engagement_data.learner_id)
        .first()
    )

    if engagement:
        # Optional: add session time incrementally
        engagement.session_minutes += engagement_data.session_minutes
        engagement.last_login = engagement_data.last_login or datetime.utcnow()
    else:
        engagement = LearnerEngagement(**engagement_data.model_dump())
        db.add(engagement)

    db.commit()
    db.refresh(engagement)
    return engagement


# =========================================================
# 🧑‍🏫 Mentor Interaction Logs
# =========================================================
def log_mentor_interaction(db: Session, interaction_data: MentorInteractionBase):
    """Log mentor interaction with learner."""
    data = interaction_data.model_dump()

    log = MentorInteractionLog(
        mentor_id=data["mentor_id"],
        learner_id=data["learner_id"],
        interaction_notes=data["interaction_notes"],
        timestamp=datetime.now(timezone.utc),
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log