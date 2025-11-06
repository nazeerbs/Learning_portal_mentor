from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from app.routers import (
    courses_router,
    mentor_router,
    lesson_router,
    modules_router,
    materials_router,
    assignment_router,
    evaluation_router,
    certificate_router,
    role_aut_router,
    Analytics_router,dashboard
)

import os

# ==============================================================
# 🧩 Database Setup
# ==============================================================
# Automatically create all database tables based on SQLAlchemy models
Base.metadata.create_all(bind=engine)

# ==============================================================
# 🚀 Initialize FastAPI App
# ==============================================================
app = FastAPI(title="Mentor-Course-Lesson Management API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================
# 🔗 Main API Router
# ==============================================================
api_router = APIRouter()
app.include_router(api_router)

# ==============================================================
# 📦 Register Routers
# ==============================================================
# Authentication & Roles
app.include_router(role_aut_router.router, prefix="/auth", tags=["Auth"])

# Certificates

# Core Course Management
app.include_router(courses_router.router, prefix="/courses", tags=["Courses"])
app.include_router(modules_router.router, prefix="/modules", tags=["Modules"])
app.include_router(lesson_router.router, prefix="/lessons", tags=["Lessons"])
app.include_router(materials_router.router, prefix="/materials", tags=["Materials"])
app.include_router(assignment_router.router, prefix="/assignments", tags=["Assignments"])

# Evaluation System
app.include_router(evaluation_router.router, prefix="/evaluation", tags=["Evaluation"])

# Mentors (optional - enable when needed)
app.include_router(mentor_router.router, prefix="/mentors", tags=["Mentors"])

# Analytics & Dashboard (future)
app.include_router(certificate_router.router, prefix="/certificates", tags=["Certificates"])
app.include_router(Analytics_router.router, prefix="/analytics", tags=["Analytics"])
app.include_router(dashboard.router, prefix="/mentor/dashboard", tags=["Dashboard"])

# ==============================================================
# 💚 Health Check Endpoint
# ==============================================================
@app.get("/", tags=["Health Check"])
def read_root():
    """Simple health check to confirm the API is running."""
    return {
        "status": "ok",
        "message": "Welcome to the GenAI99 Mentor API"
    }

# ==============================================================
# 🏁 Run the Application
# ==============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
