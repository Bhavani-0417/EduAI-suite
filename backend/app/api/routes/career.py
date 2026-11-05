import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.career_schema import (
    ResumeRequest,
    JobApplicationCreate,
    JobApplicationUpdate,
    JDMatchRequest,
)
from app.services.career.resume_builder import build_resume_pdf
from app.services.career.jd_matcher import calculate_match_score
from app.services.career.job_tracker_service import (
    add_job_application,
    get_applications,
    update_application_status,
    get_career_analytics,
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User
from app.utils.file_storage import resolve_generated_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/career", tags=["Career Center"])


@router.post("/resume/build")
def build_resume(
    request: ResumeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = build_resume_pdf(request.model_dump())
        return {
            "message": "Resume built successfully!",
            "download_url": f"/api/career/resume/download/{result['file_name']}",
            "ats_tips": result["ats_tips"],
        }
    except Exception:
        logger.exception("Resume generation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume generation failed. Please try again.",
        )


@router.get("/resume/download/{file_name}")
def download_resume(
    file_name: str,
    current_user: User = Depends(get_current_user),
):
    try:
        file_path = resolve_generated_file(file_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name.",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found.",
        ) from exc
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/pdf",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/jd-match")
def match_resume_to_jd(
    request: JDMatchRequest,
    current_user: User = Depends(get_current_user),
):
    return calculate_match_score(request.resume_text, request.job_description)


@router.post("/applications", status_code=201)
def add_application(
    data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = add_job_application(db, current_user.id, data)
    return {
        "message": "Application tracked!",
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value if hasattr(application.status, "value") else application.status,
        "match_score": application.match_score,
        "applied_date": str(application.applied_date),
    }


@router.get("/applications")
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    applications = get_applications(db, current_user.id, status)
    result = [
        {
            "id": application.id,
            "company": application.company,
            "role": application.role,
            "status": application.status.value if hasattr(application.status, "value") else application.status,
            "match_score": application.match_score,
            "applied_date": str(application.applied_date),
            "notes": application.notes,
        }
        for application in applications
    ]
    return {"total": len(result), "applications": result}


@router.put("/applications/{application_id}")
def update_application(
    application_id: str,
    data: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = update_application_status(
        db, application_id, current_user.id, data
    )
    return {
        "message": "Application updated!",
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value if hasattr(application.status, "value") else application.status,
    }


@router.delete("/applications/{application_id}")
def delete_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.career import JobApplication

    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.student_id == current_user.id,
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    db.delete(application)
    db.commit()
    return {"message": "Application deleted."}


@router.get("/analytics")
def career_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_analytics(db, current_user.id)
