# ===============================================================
# 📘 Pydantic Schemas for LMS Application (FastAPI)
# ===============================================================
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
from Base import MaterialStatusEnum, PublishStatusEnum


# ===============================================================
# USER SCHEMAS
# ===============================================================

class UserBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    role: str
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    is_active: bool
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


# ===============================================================
# AUTHENTICATION SCHEMAS
# ===============================================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    email: Optional[EmailStr] = None


# ===============================================================
# COURSE SCHEMAS
# ===============================================================

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = ""
    language: Optional[str] = "en"
    banner_url: Optional[str] = None
    batch: Optional[str] = None
    

class CourseCreate(CourseBase):
    mentor_id: int

class CourseUpdate(CourseBase):
    title: Optional[str] = None
    description: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    language: str
    publish_status: PublishStatusEnum
    banner_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    mentor: Optional[UserResponse]

    class Config:
        orm_mode = True


# ===============================================================
# MODULE SCHEMAS
# ===============================================================

class ModuleCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    position: int = 0

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None

class ModuleResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    position: int

    class Config:
        orm_mode = True

class ModuleSchema(BaseModel):
    """
    Schema for returning module details.
    """
    id: int
    course_id: int
    title: str
    description: Optional[str]
    position: int

    class Config:
        orm_mode = True
# ===============================================================
# LESSON SCHEMAS
# ===============================================================

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_type: Optional[str] = "video"
    language: Optional[str] = "en"

class LessonCreate(LessonBase):
    module_id: int

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_type: Optional[str] = None

class LessonResponse(LessonBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ===============================================================
# SUBTITLE SCHEMAS
# ===============================================================

class SubtitleSchema(BaseModel):
    id: int
    lesson_id: int
    subtitle_text: str
    language: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


# ===============================================================
# MATERIAL SCHEMAS
# ===============================================================

class MaterialCreate(BaseModel):
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    file_name: str
    file_url: str
    mime_type: Optional[str] = None
class MaterialResponse(BaseModel):
    id: int
    file_name: str
    file_url: str
    module_id: Optional[int]
    lesson_id: Optional[int]
    mime_type: Optional[str]
    preview_url: Optional[str] = None
    message: Optional[str] = None  # ✅ Add this field

    model_config = {
        "from_attributes": True  # Enables ORM conversion in Pydantic v2
    }
  
    
class MaterialUpdate(BaseModel):
    """
    Schema for updating material status.
    """
    status: MaterialStatusEnum

# ===============================================================
# ASSIGNMENT & FEEDBACK SCHEMAS
# ===============================================================

class SubmissionCreate(BaseModel):
    assignment_id: int
    student_id: int
    content: Optional[str] = None
    file_url: Optional[str] = None

class FeedbackCreate(BaseModel):
    submission_id: int
    mentor_id: int
    feedback_type: str
    feedback_content: str

class FeedbackResponse(BaseModel):
    id: int
    mentor_id: int
    feedback_type: str
    feedback_content: str
    created_at: datetime

    class Config:
        orm_mode = True

class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    content: Optional[str]
    file_url: Optional[str]
    mentor_score: Optional[int]
    ai_score: Optional[int]
    created_at: datetime
    feedbacks: List[FeedbackResponse] = []

    class Config:
        orm_mode = True

class GradeRequest(BaseModel):
    mentor_score: int = Field(..., ge=0, le=100)


# ===============================================================
# LEADERBOARD & CERTIFICATION SCHEMAS
# ===============================================================

class LeaderboardBase(BaseModel):
    student_id: int
    total_score: int
    average_score: float
    total_assignments: int
    rank: Optional[int]

    class Config:
        orm_mode = True

class CertificationBase(BaseModel):
    student_id: int
    certificate_status: str
    issue_date: Optional[datetime] = None

    class Config:
        orm_mode = True


# ===============================================================
# ANALYTICS SCHEMAS
# ===============================================================

class LearnerProgressBase(BaseModel):
    learner_id: int
    course_id: int
    progress_percent: float

class LearnerEngagementBase(BaseModel):
    learner_id: int
    session_minutes: float
    last_login: Optional[datetime] = None

class MentorInteractionBase(BaseModel):
    mentor_id: int
    learner_id: int
    interaction_notes: str


# ===============================================================
# GROUP & MENTOR ASSIGNMENT SCHEMAS
# ===============================================================

class GroupCreate(BaseModel):
    name: str
    course_id: Optional[int]

class MentorAssignmentCreate(BaseModel):
    mentor_id: int
    course_id: Optional[int] = None
    group_id: Optional[int] = None
    learner_id: Optional[int] = None

class MentorAssignmentResponse(BaseModel):
    id: int
    mentor_id: int
    learner_id: Optional[int]
    course_id: Optional[int]
    group_id: Optional[int]
    assigned_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ===============================================================
# COMMON RESPONSE SCHEMA
# ===============================================================
class ResponseMessage(BaseModel):
    message: str


class AssignmentIn(BaseModel):
    mentor_id: int
    course_id: Optional[int] = None
    group_id: Optional[int] = None
    learner_id: Optional[int] = None

class AssignmentOut(BaseModel):
    id: int
    mentor_id: int
    course_id: Optional[int]
    group_id: Optional[int]
    learner_id: Optional[int]

class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: Optional[str]
    role: str
    is_active: bool

class CourseOut(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        orm_mode = True


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: int
    module_id: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    module_id: Optional[int] = None


class AssignmentSchema(AssignmentBase):
    id: int
    file_url: Optional[str] = None
    created_at: datetime
    due_date: Optional[datetime] = None

    class Config:
        orm_mode = True

class FeedbackCreate(BaseModel):
    submission_id: int
    mentor_id: int
    feedback_type: str
    feedback_content: str


class MentorCoursesResponse(BaseModel):
    """
    Schema for returning all courses belonging to a specific mentor.
    """
    mentor_id: int
    mentor_name: str
    courses: List[CourseResponse]

    class Config:
        orm_mode = True