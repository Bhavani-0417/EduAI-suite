from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.academic import Mark
from app.models.user import User
from app.schemas.academic_schema import MarkCreate, ProfileUpdateRequest
import uuid


def add_mark(db: Session, student_id: str, data: MarkCreate) -> Mark:
    """Add a mark entry for a student"""
    mark = Mark(
        id=str(uuid.uuid4()),
        student_id=student_id,
        subject=data.subject,
        semester=data.semester,
        marks_obtained=data.marks_obtained,
        total_marks=data.total_marks,
        exam_type=data.exam_type,
    )
    db.add(mark)
    db.commit()
    db.refresh(mark)
    return mark


def get_marks(db: Session, student_id: str, semester: int = None) -> List[Mark]:
    """Get all marks for a student, optionally filtered by semester"""
    query = db.query(Mark).filter(Mark.student_id == student_id)
    if semester:
        query = query.filter(Mark.semester == semester)
    return query.order_by(Mark.semester, Mark.subject).all()


def calculate_cgpa(db: Session, student_id: str) -> dict:
    """
    Calculate CGPA from all marks.

    Formula:
    - Convert each mark to grade point (0-10 scale)
    - Average all grade points = CGPA

    Grade Scale:
    90-100 → 10 (O)
    80-89  → 9  (A+)
    70-79  → 8  (A)
    60-69  → 7  (B+)
    50-59  → 6  (B)
    40-49  → 5  (C)
    Below 40 → 0 (F)
    """
    marks = get_marks(db, student_id)

    if not marks:
        return {
            "cgpa": 0.0,
            "percentage": 0.0,
            "total_subjects": 0,
            "semester_breakdown": {}
        }

    def to_grade_point(percentage: float) -> float:
        if percentage >= 90: return 10.0
        elif percentage >= 80: return 9.0
        elif percentage >= 70: return 8.0
        elif percentage >= 60: return 7.0
        elif percentage >= 50: return 6.0
        elif percentage >= 40: return 5.0
        else: return 0.0

    total_grade_points = 0.0
    semester_breakdown = {}

    for mark in marks:
        pct = (mark.marks_obtained / mark.total_marks) * 100
        gp = to_grade_point(pct)
        total_grade_points += gp

        sem_key = f"Semester {mark.semester}"
        if sem_key not in semester_breakdown:
            semester_breakdown[sem_key] = []
        semester_breakdown[sem_key].append({
            "subject": mark.subject,
            "marks": f"{mark.marks_obtained}/{mark.total_marks}",
            "percentage": round(pct, 2),
            "grade_point": gp
        })

    cgpa = round(total_grade_points / len(marks), 2)
    overall_pct = round((cgpa / 10) * 100, 2)

    return {
        "cgpa": cgpa,
        "percentage": overall_pct,
        "total_subjects": len(marks),
        "semester_breakdown": semester_breakdown
    }


def detect_weaknesses(db: Session, student_id: str) -> dict:
    """
    Detect weak and strong subjects.

    Logic:
    - Below 50% = WEAK (needs serious attention)
    - 50-65%    = AVERAGE (needs improvement)
    - Above 65% = STRONG (doing well)
    """
    marks = get_marks(db, student_id)

    if not marks:
        return {
            "weak_subjects": [],
            "strong_subjects": [],
            "improvement_tips": {},
            "overall_grade": "N/A"
        }

    weak_subjects = []
    average_subjects = []
    strong_subjects = []

    for mark in marks:
        pct = (mark.marks_obtained / mark.total_marks) * 100
        if pct < 50:
            weak_subjects.append(mark.subject)
        elif pct < 65:
            average_subjects.append(mark.subject)
        else:
            strong_subjects.append(mark.subject)

    # Generate improvement tips for weak subjects
    improvement_tips = {}
    tip_templates = {
        "default": "Focus on fundamentals. Practice problems daily. Review class notes and textbook chapters.",
        "DBMS": "Practice SQL queries daily. Focus on normalization (1NF, 2NF, 3NF). Draw ER diagrams for real problems.",
        "OS": "Understand process scheduling algorithms. Practice memory management problems. Study deadlock conditions.",
        "CN": "Focus on OSI model layers. Practice subnetting. Understand TCP/IP thoroughly.",
        "Maths": "Practice problems daily. Focus on formulas. Solve previous year papers.",
        "ML": "Implement algorithms from scratch in Python. Focus on mathematics behind models.",
        "DSA": "Practice on LeetCode daily. Focus on time complexity. Master arrays, linked lists, trees first.",
    }

    for subject in weak_subjects + average_subjects:
        tip = tip_templates.get(subject, tip_templates["default"])
        improvement_tips[subject] = tip

    # Calculate overall grade
    all_pcts = [(m.marks_obtained / m.total_marks) * 100 for m in marks]
    avg_pct = sum(all_pcts) / len(all_pcts)

    if avg_pct >= 85: overall_grade = "A (Excellent)"
    elif avg_pct >= 70: overall_grade = "B (Good)"
    elif avg_pct >= 55: overall_grade = "C (Average)"
    elif avg_pct >= 40: overall_grade = "D (Below Average)"
    else: overall_grade = "F (Needs Serious Attention)"

    return {
        "weak_subjects": weak_subjects,
        "average_subjects": average_subjects,
        "strong_subjects": strong_subjects,
        "improvement_tips": improvement_tips,
        "overall_grade": overall_grade,
        "average_percentage": round(avg_pct, 2)
    }


def update_profile(db: Session, student: User, data: ProfileUpdateRequest) -> User:
    """Update student profile fields"""
    if data.full_name is not None:
        student.full_name = data.full_name
    if data.college_id is not None:
        student.college_id = data.college_id
    if data.year is not None:
        student.year = data.year
    if data.semester is not None:
        student.semester = data.semester
    if data.city is not None:
        student.city = data.city
    if data.profile_picture is not None:
        student.profile_picture = data.profile_picture

    db.commit()
    db.refresh(student)
    return student