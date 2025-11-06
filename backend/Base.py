"""
Comprehensive SQLAlchemy models for an LMS (Course Application).
This file builds on the provided schema and adds missing relationships,
FK constraints, Enrollment, Assignments, Activity logs, and analytics.

Assumes `Base` is imported from your `database` module and that you
use SQLAlchemy ORM (declarative) with a compatible engine.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Table,
    TIMESTAMP, Float, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum
from sqlalchemy import Enum as SQLAlchemyEnum

# --------------------------
# ENUMS
# --------------------------
class UserRole(str, enum.Enum):
    student = "student"
    mentor = "mentor"
    admin = "admin"

class PublishStatusEnum(str, enum.Enum):
    draft = "draft"
    unpublished = "unpublished"
    published = "published"

class MaterialStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# --------------------------
# ASSOCIATION TABLES
# --------------------------
mentor_student_association = Table(
    "mentor_students",
    Base.metadata,
    Column("mentor_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

course_enrollments = Table(
    "course_enrollments",
    Base.metadata,
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("enrolled_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

# --------------------------
# USER
# --------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)

    hashed_password = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Mentor <-> Student self-referential many-to-many
    supervised_students = relationship(
        "User",
        secondary=mentor_student_association,
        primaryjoin=id == mentor_student_association.c.mentor_id,
        secondaryjoin=id == mentor_student_association.c.student_id,
        backref="mentors"
    )

    # Courses created by this user (mentor)
    courses = relationship("Course", back_populates="mentor", cascade="all, delete-orphan")

    # Enrollments (many-to-many via course_enrollments)
    enrolled_courses = relationship(
        "Course",
        secondary=course_enrollments,
        back_populates="students"
    )

    # Progress & engagement
    progress = relationship("LearnerProgress", back_populates="learner", cascade="all, delete-orphan")
    engagement = relationship("LearnerEngagement", back_populates="learner", cascade="all, delete-orphan")

    # Submissions & feedbacks
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    feedbacks_given = relationship("Feedback", back_populates="mentor", foreign_keys='Feedback.mentor_id')

    # Leaderboard & certification (one-to-one semantics handled by unique constraint in models)
    leaderboard = relationship("Leaderboard", back_populates="student", uselist=False)
    certification = relationship("Certification", back_populates="student", uselist=False)

# --------------------------
# COURSE, MODULE, LESSON
# --------------------------
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(Text, default="")
    language = Column(String, default="en")
    publish_status = Column(SQLAlchemyEnum(PublishStatusEnum), default=PublishStatusEnum.draft)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    mentor = relationship("User", back_populates="courses", foreign_keys=[mentor_id])

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")

    banner_url = Column(String, nullable=True)
    batch = Column(String, nullable=True)

    # students via many-to-many
    students = relationship(
        "User",
        secondary=course_enrollments,
        back_populates="enrolled_courses"
    )

    # groups and assignments
    groups = relationship("Group", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    progress = relationship("LearnerProgress", back_populates="course", cascade="all, delete-orphan")

# Module
class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="module", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="module", cascade="all, delete-orphan")

# Lesson
class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_url = Column(String, nullable=True)
    content_type = Column(String(50), default="video")
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    module = relationship("Module", back_populates="lessons")
    subtitles = relationship("LessonSubtitle", back_populates="lesson", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="lesson", cascade="all, delete-orphan")

# LessonSubtitle
class LessonSubtitle(Base):
    __tablename__ = "lesson_subtitles"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"))
    subtitle_text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="generated")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    subtitle_url = Column(String, nullable=True)

    lesson = relationship("Lesson", back_populates="subtitles")

# Material
class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(MaterialStatusEnum), default=MaterialStatusEnum.pending)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    module = relationship("Module", back_populates="materials", foreign_keys=[module_id])
    lesson = relationship("Lesson", back_populates="materials", foreign_keys=[lesson_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])

# --------------------------
# ASSIGNMENTS, SUBMISSIONS, FEEDBACK
# --------------------------
class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    file_url = Column(String, nullable=True)  # ✅ Added field for uploaded file
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="assignments")
    module = relationship("Module", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True)
    file_url = Column(String, nullable=True)

    # ✅ AI grading fields
    ai_score = Column(Integer, nullable=True)
    ai_feedback = Column(Text, nullable=True)   # <-- Add this field to fix the error

    # ✅ Mentor override fields
    mentor_score = Column(Integer, nullable=True)
    mentor_feedback = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    feedbacks = relationship("Feedback", back_populates="submission", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "submission_feedback"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"))
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    feedback_type = Column(String, nullable=True)  # 'text', 'audio', 'video'
    feedback_content = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    submission = relationship("Submission", back_populates="feedbacks")
    mentor = relationship("User", back_populates="feedbacks_given", foreign_keys=[mentor_id])

# Leaderboard & Certification
class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    total_score = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    total_assignments = Column(Integer, default=0)
    rank = Column(Integer, nullable=True)

    student = relationship("User", back_populates="leaderboard")

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    certificate_status = Column(String, default="Not Qualified")
    issue_date = Column(TIMESTAMP, nullable=True)
    file_url = Column(String, nullable=True)  # ✅ Add this line
    student = relationship("User", back_populates="certification")

# --------------------------
# ANALYTICS & ENGAGEMENT
# --------------------------
class LearnerProgress(Base):
    __tablename__ = "learner_progress"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    progress_percent = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    learner = relationship("User", back_populates="progress")
    course = relationship("Course", back_populates="progress")

class LearnerEngagement(Base):
    __tablename__ = "learner_engagement"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    session_minutes = Column(Float, default=0.0)
    last_login = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    learner = relationship("User", back_populates="engagement")

class MentorInteractionLog(Base):
    __tablename__ = "mentor_logs"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    learner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    interaction_notes = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    mentor = relationship("User", foreign_keys=[mentor_id])
    learner = relationship("User", foreign_keys=[learner_id])

# --------------------------
# GROUPS & MENTOR ASSIGNMENTS
# --------------------------
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

    course = relationship("Course", back_populates="groups")

class MentorAssignment(Base):
    __tablename__ = "mentor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    learner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "mentor_id",
            "course_id",
            "group_id",
            "learner_id",
            name="_mentor_assign_uc",
        ),
    )

    mentor = relationship("User", foreign_keys=[mentor_id], backref="mentor_assignments")
    learner = relationship("User", foreign_keys=[learner_id], backref="learner_assignments")
    course = relationship("Course", foreign_keys=[course_id], backref="mentor_assignments")
    group = relationship("Group", foreign_keys=[group_id], backref="mentor_assignments")

# --------------------------
# ACTIVITY & QUIZZES (OPTIONAL)
# --------------------------
# class ActivityLog(Base):
#     __tablename__ = "activity_logs"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
#     course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
#     module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
#     lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
#     action = Column(String(128))  # e.g., 'viewed_lesson', 'submitted_assignment'
#     metadata = Column(Text, nullable=True)  # JSON string for extra info
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     user = relationship("User")
#     course = relationship("Course")
#     module = relationship("Module")
#     lesson = relationship("Lesson")

# class Quiz(Base):
#     __tablename__ = "quizzes"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, nullable=False)
#     course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True)
#     module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")

# class QuizQuestion(Base):
#     __tablename__ = "quiz_questions"

#     id = Column(Integer, primary_key=True, index=True)
#     quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))
#     question_text = Column(Text, nullable=False)
#     # For simplicity: store options & answer as JSON/text; a richer model may normalize options
#     options = Column(Text, nullable=True)
#     correct_answer = Column(String, nullable=True)

#     quiz = relationship("Quiz", back_populates="questions")

# class QuizResponse(Base):
#     __tablename__ = "quiz_responses"

#     id = Column(Integer, primary_key=True, index=True)
#     quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
#     score = Column(Float, nullable=True)
#     responses = Column(Text, nullable=True)  # JSON text of answers
#     submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     quiz = relationship("Quiz")
#     user = relationship("User")

# --------------------------
# AGGREGATED ANALYTICS (OPTIONAL)
# --------------------------
# class CourseAnalytics(Base):
#     __tablename__ = "course_analytics"

#     id = Column(Integer, primary_key=True, index=True)
#     course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
#     average_progress = Column(Float, default=0.0)
#     completion_rate = Column(Float, default=0.0)
#     active_students = Column(Integer, default=0)
#     snapshot_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#     course = relationship("Course")

# End of file
