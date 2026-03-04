from sqlalchemy.orm import Session
from app.models.college import College
from app.models.user import User
from app.schemas.template_schema import CollegeTemplate


# Default template used when student has no college
DEFAULT_TEMPLATE = CollegeTemplate(
    college_name="EduAI Suite",
    primary_color="#1E3A5F",
    secondary_color="#2E75B6",
    logo_url=None,
    header_text="EduAI Suite",
    footer_text="AI-Powered Academic Platform",
    font_name="Arial",
    watermark_text="EduAI Suite"
)


def get_college_template(db: Session, student: User) -> CollegeTemplate:
    """
    Fetch the college template for a student.

    Logic:
    1. Check if student has a college_id
    2. Fetch college from DB
    3. Build CollegeTemplate from college fields
    4. If no college → use default EduAI template
    """
    if not student.college_id:
        print("⚠️  No college linked — using default template")
        return DEFAULT_TEMPLATE

    college = db.query(College).filter(
        College.id == student.college_id
    ).first()

    if not college:
        print("⚠️  College not found — using default template")
        return DEFAULT_TEMPLATE

    template = CollegeTemplate(
        college_name=college.name or "My College",
        primary_color=getattr(college, 'primary_color', None) or "#1E3A5F",
        secondary_color=getattr(college, 'secondary_color', None) or "#2E75B6",
        logo_url=getattr(college, 'logo_url', None),
        header_text=getattr(college, 'header_text', None) or college.name,
        footer_text=getattr(college, 'footer_text', None) or college.university or "",
        font_name=getattr(college, 'font_name', None) or "Arial",
        watermark_text=getattr(college, 'watermark_text', None) or college.name
    )

    print(f"✅ Loaded template for: {template.college_name}")
    return template


def update_college_template(
    db: Session,
    college_id: str,
    data: dict
) -> College:
    """Update template settings for a college"""
    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found."
        )

    for field, value in data.items():
        if value is not None and hasattr(college, field):
            setattr(college, field, value)

    db.commit()
    db.refresh(college)
    return college