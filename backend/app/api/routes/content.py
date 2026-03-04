import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.schemas.template_schema import TemplatePPTRequest, TemplateDocRequest, CollegeTemplateUpdate
from app.services.content.template_service import get_college_template, update_college_template
from app.services.content.template_ppt_service import generate_college_ppt
from app.services.content.template_doc_service import generate_college_document
from app.db.database import get_db
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
@router.post("/generate/ppt/college-template")
def create_college_ppt(
    request: TemplatePPTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PPT using student's college template.

    POST /api/content/generate/ppt/college-template

    Automatically fetches:
    - College colors, logo, header, footer
    - Applies full branding to every slide

    If student has no college linked → uses EduAI default theme.
    """
    try:
        # Fetch college template
        template = get_college_template(db, current_user)

        result = generate_college_ppt(
            topic=request.topic,
            template=template,
            num_slides=request.num_slides,
            key_points=request.key_points,
            subject=request.subject,
            include_speaker_notes=request.include_speaker_notes,
            student_name=current_user.full_name
        )

        return {
            "message": "College-branded PPT generated!",
            "topic": request.topic,
            "num_slides": result["num_slides"],
            "template_used": result["template_used"],
            "download_url": f"/api/content/download/ppt/{result['file_name']}",
            "slides_preview": result["slides_preview"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"College PPT generation failed: {str(e)}"
        )


@router.post("/generate/document/college-template")
def create_college_document(
    request: TemplateDocRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate document using student's college template.

    POST /api/content/generate/document/college-template

    Applies college branding:
    - College header on every page
    - College footer with page numbers
    - College colors for headings
    - Professional cover page with college name
    """
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
            include_references=request.include_references
        )

        return {
            "message": "College-branded document generated!",
            "title": request.title,
            "doc_type": request.doc_type.value,
            "template_used": result["template_used"],
            "word_count": result["word_count"],
            "download_url": f"/api/content/download/doc/{result['file_name']}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"College document generation failed: {str(e)}"
        )


@router.put("/college-template/{college_id}")
def update_template(
    college_id: str,
    data: CollegeTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update college template settings.

    PUT /api/content/college-template/{college_id}
    Body: { primary_color, secondary_color, logo_url, header_text, footer_text }

    Use this to set your college's official colors and logo.
    Example colors:
      JNTU   → primary: #003366
      VTU    → primary: #8B0000
      Anna U → primary: #006400
    """
    college = update_college_template(
        db, college_id, data.model_dump(exclude_none=True)
    )
    return {
        "message": "College template updated!",
        "college": college.name,
        "primary_color": getattr(college, 'primary_color', '#1E3A5F'),
        "secondary_color": getattr(college, 'secondary_color', '#2E75B6')
    }