from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.college import College
from app.schemas.college_schema import CollegeCreate
import uuid


def create_college(db: Session, data: CollegeCreate) -> College:
    """Create a new college"""
    # Check college code not duplicate
    if data.college_code:
        existing = db.query(College).filter(
            College.college_code == data.college_code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="College with this code already exists."
            )

    college = College(
        id=str(uuid.uuid4()),
        name=data.name,
        university=data.university,
        city=data.city,
        state=data.state,
        college_code=data.college_code,
    )
    db.add(college)
    db.commit()
    db.refresh(college)
    return college


def get_all_colleges(db: Session, search: str = None) -> list:
    """Get all colleges, optionally filtered by search term"""
    query = db.query(College)

    if search:
        # Search by name or city
        query = query.filter(
            College.name.ilike(f"%{search}%") |
            College.city.ilike(f"%{search}%") |
            College.university.ilike(f"%{search}%")
        )

    return query.order_by(College.name).all()


def get_college_by_id(db: Session, college_id: str) -> College:
    """Get a single college by ID"""
    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found."
        )
    return college


def seed_colleges(db: Session):
    """
    Add some Indian colleges as initial data.
    Called once to populate the database.
    """
    colleges_data = [
        {"name": "IIT Bombay", "university": "IIT Bombay", "city": "Mumbai", "state": "Maharashtra", "college_code": "IITB"},
        {"name": "IIT Delhi", "university": "IIT Delhi", "city": "Delhi", "state": "Delhi", "college_code": "IITD"},
        {"name": "JNTU Hyderabad", "university": "JNTU", "city": "Hyderabad", "state": "Telangana", "college_code": "JNTUH"},
        {"name": "VTU Belgaum", "university": "VTU", "city": "Belgaum", "state": "Karnataka", "college_code": "VTU"},
        {"name": "Anna University", "university": "Anna University", "city": "Chennai", "state": "Tamil Nadu", "college_code": "AU"},
        {"name": "Mumbai University", "university": "Mumbai University", "city": "Mumbai", "state": "Maharashtra", "college_code": "MU"},
        {"name": "Osmania University", "university": "Osmania University", "city": "Hyderabad", "state": "Telangana", "college_code": "OU"},
        {"name": "SMEC", "university": "JNTU", "city": "Hyderabad", "state": "Telangana", "college_code": "SMEC"},
    ]

    for data in colleges_data:
        existing = db.query(College).filter(
            College.college_code == data["college_code"]
        ).first()
        if not existing:
            college = College(id=str(uuid.uuid4()), **data)
            db.add(college)

    db.commit()
    print("✅ Colleges seeded successfully")