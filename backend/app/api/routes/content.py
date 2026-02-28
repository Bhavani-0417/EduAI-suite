import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.content_schema import (
    PPTRequest, DocumentRequest
)
from app.services.content.ppt_service import generate_ppt
from app.services.content.doc_service import generate_document
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/content",
    tags=["Content Generator"]
)


@router.post("/generate/ppt")
def create_ppt(
    request: PPTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI-powered PowerPoint presentation.

    POST /api/content/generate/ppt
    Body: { topic, num_slides, style, key_points, subject }

    Flow:
    1. LangChain plans slides
    2. python-pptx builds file
    3. Returns download URL + preview
    """
    try:
        result = generate_ppt(
            topic=request.topic,
            num_slides=request.num_slides,
            style=request.style.value,
            key_points=request.key_points,
            subject=request.subject,
            include_speaker_notes=request.include_speaker_notes,
            student_name=current_user.full_name
        )

        return {
            "message": "PPT generated successfully!",
            "topic": request.topic,
            "num_slides": result["num_slides"],
            "download_url": f"/api/content/download/ppt/{result['file_name']}",
            "slides_preview": result["slides_preview"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PPT generation failed: {str(e)}"
        )


@router.post("/generate/document")
def create_document(
    request: DocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI-powered Word document.

    POST /api/content/generate/document
    Body: { title, topic, doc_type, key_points, subject }
    """
    try:
        result = generate_document(
            title=request.title,
            topic=request.topic,
            doc_type=request.doc_type.value,
            key_points=request.key_points,
            subject=request.subject,
            student_name=request.student_name or current_user.full_name,
            college_name=request.college_name,
            include_references=request.include_references
        )

        return {
            "message": "Document generated successfully!",
            "title": request.title,
            "doc_type": request.doc_type.value,
            "download_url": f"/api/content/download/doc/{result['file_name']}",
            "word_count": result["word_count"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {str(e)}"
        )


@router.get("/download/ppt/{file_name}")
def download_ppt(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download a generated PPT file.

    GET /api/content/download/ppt/{file_name}
    Returns the actual .pptx file for download.
    """
    file_path = os.path.join("generated_files", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or expired."
        )

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


@router.get("/download/doc/{file_name}")
def download_doc(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download a generated Word document.

    GET /api/content/download/doc/{file_name}
    Returns the actual .docx file for download.
    """
    file_path = os.path.join("generated_files", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or expired."
        )

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )