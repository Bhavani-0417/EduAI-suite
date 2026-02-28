from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from collections import Counter
from datetime import datetime
import uuid

from app.models.career import JobApplication, ApplicationStatus
from app.schemas.career_schema import JobApplicationCreate, JobApplicationUpdate
from app.services.career.jd_matcher import calculate_match_score


def add_job_application(
    db: Session,
    student_id: str,
    data: JobApplicationCreate
) -> JobApplication:
    """Add a new job application to tracker"""

    # Auto-calculate match score if JD provided
    match_score = None
    if data.job_description and data.resume_version_url:
        try:
            match_result = calculate_match_score(
                data.resume_version_url,   # using as text for now
                data.job_description
            )
            match_score = match_result["match_score"]
        except:
            match_score = None

    application = JobApplication(
        id=str(uuid.uuid4()),
        student_id=student_id,
        company=data.company,
        role=data.role,
        job_description=data.job_description,
        resume_version_url=data.resume_version_url,
        match_score=match_score,
        notes=data.notes,
        status=ApplicationStatus.APPLIED
    )

    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_applications(
    db: Session,
    student_id: str,
    status_filter: str = None
) -> list:
    """Get all job applications for a student"""
    query = db.query(JobApplication).filter(
        JobApplication.student_id == student_id
    )

    if status_filter:
        query = query.filter(
            JobApplication.status == status_filter
        )

    return query.order_by(JobApplication.applied_date.desc()).all()


def update_application_status(
    db: Session,
    application_id: str,
    student_id: str,
    data: JobApplicationUpdate
) -> JobApplication:
    """Update status or notes of an application"""
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.student_id == student_id
    ).first()

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    if data.status:
        app.status = data.status.value
    if data.notes is not None:
        app.notes = data.notes

    db.commit()
    db.refresh(app)
    return app


def get_career_analytics(db: Session, student_id: str) -> dict:
    """
    Generate career analytics for the student.

    Calculates:
    - Total applications
    - Status breakdown (applied, interview, offer etc.)
    - Response rate
    - Most applied roles and companies
    - Average match score
    - Monthly application trend
    """
    applications = get_applications(db, student_id)

    if not applications:
        return {
            "total_applications": 0,
            "status_breakdown": {},
            "response_rate": 0.0,
            "top_roles": [],
            "top_companies": [],
            "average_match_score": 0.0,
            "monthly_applications": {}
        }

    total = len(applications)

    # Status breakdown
    status_counts = Counter(app.status for app in applications)
    status_breakdown = {
        str(k.value if hasattr(k, 'value') else k): v
        for k, v in status_counts.items()
    }

    # Response rate — anything beyond "applied" counts as response
    responses = sum(
        1 for app in applications
        if app.status != ApplicationStatus.APPLIED
        and app.status != "applied"
    )
    response_rate = round((responses / total) * 100, 1)

    # Top roles and companies
    roles = Counter(app.role for app in applications)
    companies = Counter(app.company for app in applications)

    top_roles = [role for role, _ in roles.most_common(5)]
    top_companies = [co for co, _ in companies.most_common(5)]

    # Average match score
    scores = [
        app.match_score for app in applications
        if app.match_score is not None
    ]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Monthly trend
    monthly = Counter()
    for app in applications:
        if app.applied_date:
            month_key = app.applied_date.strftime("%b %Y")
            monthly[month_key] += 1

    return {
        "total_applications": total,
        "status_breakdown": status_breakdown,
        "response_rate": response_rate,
        "top_roles": top_roles,
        "top_companies": top_companies,
        "average_match_score": avg_score,
        "monthly_applications": dict(monthly)
    }