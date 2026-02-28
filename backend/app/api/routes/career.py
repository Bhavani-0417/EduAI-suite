from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.db.database import get_db
from app.schemas.career_schema import (
    ResumeRequest,
    JobApplicationCreate,
    JobApplicationUpdate,
    JDMatchRequest
)
from app.services.career.resume_builder import build_resume_pdf
from app.services.career.jd_matcher import calculate_match_score
from app.services.career.job_tracker_service import (
    add_job_application,
    get_applications,
    update_application_status,
    get_career_analytics
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/career",
    tags=["Career Center"]
)


# ─────────────────────────────────────────
# RESUME BUILDER
# ─────────────────────────────────────────

@router.post("/resume/build")
def build_resume(
    request: ResumeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Build an ATS-optimized PDF resume.

    POST /api/career/resume/build
    Body: full resume data (education, skills, projects etc.)

    AI optimizes:
    - Objective statement
    - Project descriptions
    - ATS improvement tips
    """
    try:
        resume_data = request.model_dump()
        result = build_resume_pdf(resume_data)

        return {
            "message": "Resume built successfully!",
            "download_url": f"/api/career/resume/download/{result['file_name']}",
            "ats_tips": result["ats_tips"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume generation failed: {str(e)}"
        )


@router.get("/resume/download/{file_name}")
def download_resume(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """Download a generated resume PDF"""
    file_path = os.path.join("generated_files", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found."
        )

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/pdf"
    )


# ─────────────────────────────────────────
# JD MATCHER
# ─────────────────────────────────────────

@router.post("/jd-match")
def match_resume_to_jd(
    request: JDMatchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Match a resume against a job description.

    POST /api/career/jd-match
    Body: { resume_text, job_description }

    Returns:
    - match_score: 0-100
    - matched_skills: what you have
    - missing_skills: what you need
    - recommendation: AI advice
    """
    result = calculate_match_score(
        request.resume_text,
        request.job_description
    )
    return result


# ─────────────────────────────────────────
# JOB APPLICATION TRACKER
# ─────────────────────────────────────────

@router.post("/applications", status_code=201)
def add_application(
    data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new job application to tracker.

    POST /api/career/applications
    Body: { company, role, job_description, notes }
    """
    app = add_job_application(db, current_user.id, data)
    return {
        "message": "Application tracked!",
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "status": app.status.value if hasattr(app.status, 'value') else app.status,
        "match_score": app.match_score,
        "applied_date": str(app.applied_date)
    }


@router.get("/applications")
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all job applications, optionally filtered by status"""
    applications = get_applications(db, current_user.id, status)

    result = []
    for app in applications:
        result.append({
            "id": app.id,
            "company": app.company,
            "role": app.role,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "match_score": app.match_score,
            "applied_date": str(app.applied_date),
            "notes": app.notes
        })

    return {"total": len(result), "applications": result}


@router.put("/applications/{application_id}")
def update_application(
    application_id: str,
    data: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update application status or notes.

    PUT /api/career/applications/{id}
    Body: { status, notes }

    Use this when you get shortlisted, interview, offer, or rejected.
    """
    app = update_application_status(
        db, application_id, current_user.id, data
    )
    return {
        "message": "Application updated!",
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "status": app.status.value if hasattr(app.status, 'value') else app.status
    }


@router.delete("/applications/{application_id}")
def delete_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job application from tracker"""
    from app.models.career import JobApplication

    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.student_id == current_user.id
    ).first()

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    db.delete(app)
    db.commit()
    return {"message": "Application deleted."}


# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

@router.get("/analytics")
def career_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get career analytics dashboard data.

    GET /api/career/analytics

    Returns:
    - Total applications
    - Status breakdown
    - Response rate
    - Top companies and roles
    - Average match score
    - Monthly trend
    """
    return get_career_analytics(db, current_user.id)