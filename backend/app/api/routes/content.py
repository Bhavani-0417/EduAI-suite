import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.template_schema import TemplatePPTRequest, TemplateDocRequest, CollegeTemplateUpdate
from app.services.content.template_service import get_college_template, update_college_template
from app.services.content.template_ppt_service import generate_college_ppt
from app.services.content.template_doc_service import generate_college_document
from app.db.database import get_db
from app.schemas.content_schema import PPTRequest, DocumentRequest
from app.services.content.ppt_service import generate_ppt
from app.services.content.doc_service import generate_document
from app.api.middlewares.auth_middleware import get_current_user, require_admin
from app.models.user import User
from app.utils.file_storage import resolve_generated_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/content", tags=["Content Generator"])


def _resolve_download(file_name: str) -> str:
    try:
        return resolve_generated_file(file_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name.",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or expired.",
        ) from exc


@router.post("/generate/ppt")
def create_ppt(
    request: PPTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = generate_ppt(
            topic=request.topic,
            num_slides=request.num_slides,
            style=request.style.value,
            key_points=request.key_points,
            subject=request.subject,
            include_speaker_notes=request.include_speaker_notes,
            student_name=current_user.full_name,
        )
        return {
            "message": "PPT generated successfully!",
            "topic": request.topic,
            "num_slides": result["num_slides"],
            "download_url": f"/api/content/download/ppt/{result['file_name']}",
            "slides_preview": result["slides_preview"],
        }
    except Exception:
        logger.exception("PPT generation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PPT generation failed. Please try again.",
        )


@router.post("/generate/document")
def create_document(
    request: DocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = generate_document(
            title=request.title,
            topic=request.topic,
            doc_type=request.doc_type.value,
            key_points=request.key_points,
            subject=request.subject,
            student_name=request.student_name or current_user.full_name,
            college_name=request.college_name,
            include_references=request.include_references,
        )
        return {
            "message": "Document generated successfully!",
            "title": request.title,
            "doc_type": request.doc_type.value,
            "download_url": f"/api/content/download/doc/{result['file_name']}",
            "word_count": result["word_count"],
        }
    except Exception:
        logger.exception("Document generation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document generation failed. Please try again.",
        )


@router.get("/download/ppt/{file_name}")
def download_ppt(
    file_name: str,
    current_user: User = Depends(get_current_user),
):
    file_path = _resolve_download(file_name)
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/download/doc/{file_name}")
def download_doc(
    file_name: str,
    current_user: User = Depends(get_current_user),
):
    file_path = _resolve_download(file_name)
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/generate/ppt/college-template")
def create_college_ppt(
    request: TemplatePPTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        template = get_college_template(db, current_user)
        result = generate_college_ppt(
            topic=request.topic,
            template=template,
            num_slides=request.num_slides,
            key_points=request.key_points,
            subject=request.subject,
            include_speaker_notes=request.include_speaker_notes,
            student_name=current_user.full_name,
        )
        return {
            "message": "College-branded PPT generated!",
            "topic": request.topic,
            "num_slides": result["num_slides"],
            "template_used": result["template_used"],
            "download_url": f"/api/content/download/ppt/{result['file_name']}",
            "slides_preview": result["slides_preview"],
        }
    except Exception:
        logger.exception("College PPT generation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="College PPT generation failed. Please try again.",
        )


@router.post("/generate/document/college-template")
def create_college_document(
    request: TemplateDocRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        template = get_college_template(db, current_user)
        result = generate_college_document(
            title=request.title,
            topic=request.topic,
            doc_type=request.doc_type.value,
            template=template,
            key_points=request.key_points,
            subject=request.subject,
            student_name=current_user.full_name,
            include_references=request.include_references,
        )
        return {
            "message": "College-branded document generated!",
            "title": request.title,
            "doc_type": request.doc_type.value,
            "template_used": result["template_used"],
            "word_count": result["word_count"],
            "download_url": f"/api/content/download/doc/{result['file_name']}",
        }
    except Exception:
        logger.exception("College document generation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="College document generation failed. Please try again.",
        )


@router.put("/college-template/{college_id}")
def update_template(
    college_id: str,
    data: CollegeTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update college branding. Restricted to administrators."""
    college = update_college_template(
        db, college_id, data.model_dump(exclude_none=True)
    )
    return {
        "message": "College template updated!",
        "college": college.name,
        "primary_color": getattr(college, "primary_color", "#1E3A5F"),
        "secondary_color": getattr(college, "secondary_color", "#2E75B6"),
    }
