from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.middlewares.auth_middleware import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.college_schema import CollegeCreate, CollegeListResponse, CollegeResponse
from app.services.college_service import (
    create_college,
    get_all_colleges,
    get_college_by_id,
    seed_colleges,
)

router = APIRouter(prefix="/api/colleges", tags=["Colleges"])


@router.get("/", response_model=CollegeListResponse)
def list_colleges(
    search: Optional[str] = Query(None, description="Search by name, city or university"),
    db: Session = Depends(get_db),
):
    """Public college list used by the account registration form."""
    colleges = get_all_colleges(db, search)
    return CollegeListResponse(total=len(colleges), colleges=colleges)


@router.get("/{college_id}", response_model=CollegeResponse)
def get_college(college_id: str, db: Session = Depends(get_db)):
    return get_college_by_id(db, college_id)


@router.post("/", response_model=CollegeResponse, status_code=201)
def add_college(
    data: CollegeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a college. Restricted to administrators."""
    return create_college(db, data)


@router.post("/seed", status_code=201)
def seed(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Seed initial college data. Restricted to administrators."""
    seed_colleges(db)
    return {"message": "Colleges seeded successfully!"}
