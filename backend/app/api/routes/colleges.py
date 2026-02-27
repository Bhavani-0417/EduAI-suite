from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.college_schema import CollegeCreate, CollegeResponse, CollegeListResponse
from app.services.college_service import (
    create_college, get_all_colleges, get_college_by_id, seed_colleges
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/colleges",
    tags=["Colleges"]
)


@router.get("/", response_model=CollegeListResponse)
def list_colleges(
    search: Optional[str] = Query(None, description="Search by name, city or university"),
    db: Session = Depends(get_db)
):
    """
    Get all colleges. Optionally search by name/city.
    Public endpoint — no login needed.
    Used in registration dropdown.
    """
    colleges = get_all_colleges(db, search)
    return CollegeListResponse(
        total=len(colleges),
        colleges=colleges
    )


@router.get("/{college_id}", response_model=CollegeResponse)
def get_college(college_id: str, db: Session = Depends(get_db)):
    """Get a single college by its ID"""
    return get_college_by_id(db, college_id)


@router.post("/", response_model=CollegeResponse, status_code=201)
def add_college(
    data: CollegeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new college. Requires login.
    In production this would be admin-only.
    """
    return create_college(db, data)


@router.post("/seed", status_code=201)
def seed(db: Session = Depends(get_db)):
    """
    Seed initial college data.
    Run this ONCE to populate colleges table.
    """
    seed_colleges(db)
    return {"message": "Colleges seeded successfully!"}