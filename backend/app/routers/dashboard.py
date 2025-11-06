from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from Base import Course, User, UserRole, Submission, Assignment,LearnerProgress

router = APIRouter()

# ✅ 1. Dashboard Combined Endpoint
@router.get("/")
def get_dashboard_data(db: Session = Depends(get_db)):
    # Fetch published courses
    courses = db.query(Course).filter(Course.publish_status == "published").all()

    # Fetch students only
    students = db.query(User).filter(User.role == UserRole.student).all()
    students_data = [
        {
            "id": s.id,
            "name": f"{s.first_name} {s.last_name or ''}".strip(),
            "email": s.email,
            "coursesEnrolled": len(s.enrolled_courses),
            "progress": 0,
            "lastActivity": None,
        }
        for s in students
    ]

    # Stats
    stats = {
        "enrolledCourses": len(courses),
        "activeCourses": len(courses),
        "completedCourses": 0,
        "totalStudents": len(students),
        "pendingEvaluations": db.query(Submission).filter(Submission.mentor_score == None).count(),
        "upcomingSessions": 0
    }

    # Course Data
    courses_data = [
        {
            "id": c.id,
            "title": c.title,
            "image": c.banner_url or "/placeholder.png",
            "students": len(c.students),
            "progress": 0,
        }
        for c in courses
    ]

    # Pending Evaluations
    pending_subs = db.query(Submission).filter(Submission.mentor_score == None).all()
    evaluations = []
    for ev in pending_subs:
        student = db.query(User).filter(User.id == ev.student_id).first()
        assignment = db.query(Assignment).filter(Assignment.id == ev.assignment_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first()

        evaluations.append({
            "id": ev.id,
            "studentName": f"{student.first_name} {student.last_name}",
            "course": course.title,
            "assignment": assignment.title,
            "status": "Pending"
        })

    return {
        "stats": stats,
        "students": students_data,
        "courses": courses_data,
        "evaluations": evaluations,
        "sessions": [],
        "messages": [],
        "insights": {
            "progressData": [],
            "engagementData": []
        }
    }


# ✅ 2. Standalone — Total Students
@router.get("/students")
def get_total_students(db: Session = Depends(get_db)):
    total = db.query(User).filter(User.role == UserRole.student).count()
    return {"totalStudents": total}


# ✅ 3. Standalone — Courses Only
@router.get("/courses")
def get_courses_only(db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.publish_status == "published").all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "image": c.banner_url or "/placeholder.png",
            "students": len(c.students),
            "progress": 0
        }
        for c in courses
    ]


# ✅ 4. Standalone — Pending Evaluations
@router.get("/evaluations")
def get_pending_evaluations(db: Session = Depends(get_db)):
    pending = db.query(Submission).filter(Submission.mentor_score == None).all()
    evaluations = []

    for ev in pending:
        student = db.query(User).filter(User.id == ev.student_id).first()
        assignment = db.query(Assignment).filter(Assignment.id == ev.assignment_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first()

        evaluations.append({
            "id": ev.id,
            "studentName": f"{student.first_name} {student.last_name}",
            "course": course.title,
            "assignment": assignment.title,
            "status": "Pending"
        })

    return evaluations


@router.get("/insights")
def get_dashboard_insights(db: Session = Depends(get_db)):
    """
    Dashboard Insights API:
    - Monthly progressData for all learners
    - Course-wise engagementData
    """

    # ✅ Fetch students
    learners = db.query(User).filter(User.role == "student").all()
    learner_progress = db.query(LearnerProgress).all()

    # ✅ Fetch courses
    courses = db.query(Course).filter(Course.publish_status == "published").all()

    # ---------------------------------------------------
    # 📌 1) PROGRESS DATA (Monthly Overview)
    # ---------------------------------------------------
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    progressData = []

    for month in months:
        data_row = {"month": month}

        for learner in learners:

            # Get learner progress record
            prog = next(
                (p.progress_percent for p in learner_progress if p.learner_id == learner.id),
                0
            )

            # Use first name as graph key
            key = learner.first_name.lower()

            data_row[key] = prog

        progressData.append(data_row)

    # ---------------------------------------------------
    # 📌 2) ENGAGEMENT DATA (Course Activity)
    # ---------------------------------------------------
    engagementData = []

    for course in courses:
        total_students = len(course.students)

        engagementData.append({
            "course": course.title,
            "timeSpent": total_students * 12,       # dummy logic
            "interactions": total_students * 5      # dummy logic
        })

    return {
        "progressData": progressData,
        "engagementData": engagementData
    }
