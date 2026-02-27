from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.schemas.academic_schema import (
    MarkCreate, MarkResponse, CGPAResponse,
    WeaknessReport, ProfileUpdateRequest
)
from app.schemas.auth_schema import UserResponse
from app.services.academic_service import (
    add_mark, get_marks, calculate_cgpa,
    detect_weaknesses, update_profile
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/academic",
    tags=["Academic"]
)


@router.post("/marks", status_code=201)
def add_marks(
    data: MarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a mark entry.
    POST /api/academic/marks
    Requires login. Saves to logged-in student's account.
    """
    mark = add_mark(db, current_user.id, data)
    pct = round((mark.marks_obtained / mark.total_marks) * 100, 2)
    return {
        "message": "Mark added successfully!",
        "id": mark.id,
        "subject": mark.subject,
        "semester": mark.semester,
        "marks_obtained": mark.marks_obtained,
        "total_marks": mark.total_marks,
        "percentage": pct,
        "exam_type": mark.exam_type
    }


@router.get("/marks")
def view_marks(
    semester: Optional[int] = Query(None, description="Filter by semester"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all marks for logged-in student.
    Optionally filter by semester number.
    """
    marks = get_marks(db, current_user.id, semester)
    result = []
    for mark in marks:
        pct = round((mark.marks_obtained / mark.total_marks) * 100, 2)
        result.append({
            "id": mark.id,
            "subject": mark.subject,
            "semester": mark.semester,
            "marks_obtained": mark.marks_obtained,
            "total_marks": mark.total_marks,
            "percentage": pct,
            "exam_type": mark.exam_type
        })
    return {"total": len(result), "marks": result}


@router.get("/cgpa")
def get_cgpa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate and return CGPA for logged-in student.
    Automatically computes from all stored marks.
    """
    return calculate_cgpa(db, current_user.id)


@router.get("/weakness")
def get_weakness_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get weakness analysis report.
    Shows weak, average, strong subjects with improvement tips.
    """
    return detect_weaknesses(db, current_user.id)


@router.put("/profile", response_model=UserResponse)
def update_my_profile(
    data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update logged-in student's profile.
    Only provided fields are updated.
    """
    updated = update_profile(db, current_user, data)
    return UserResponse.model_validate(updated)