import io
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.vault.vault_service import (
    upload_vault_document, get_vault_documents,
    download_vault_document, generate_share_link,
    download_via_share_token
)
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/vault",
    tags=["Document Vault"]
)


@router.post("/upload", status_code=201)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Query("other", description="marksheet/certificate/transcript/id_card/offer_letter/other"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and encrypt a document to vault.

    POST /api/vault/upload?doc_type=certificate
    Body: multipart file upload

    File is AES encrypted before saving.
    OCR text extracted for search.
    """
    doc = upload_vault_document(db, current_user.id, file, doc_type)

    return {
        "message": "Document encrypted and stored in vault!",
        "id": doc.id,
        "file_name": doc.file_name,
        "doc_type": doc.doc_type.value if hasattr(doc.doc_type, 'value') else doc.doc_type,
        "has_ocr_text": bool(doc.ocr_text),
        "created_at": str(doc.created_at)
    }


@router.get("/")
def list_documents(
    doc_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents in vault"""
    docs = get_vault_documents(db, current_user.id, doc_type)

    return {
        "total": len(docs),
        "documents": [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "doc_type": doc.doc_type.value if hasattr(doc.doc_type, 'value') else doc.doc_type,
                "has_ocr_text": bool(doc.ocr_text),
                "has_share_link": bool(doc.share_token),
                "created_at": str(doc.created_at)
            }
            for doc in docs
        ]
    }


@router.get("/download/{doc_id}")
def download_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download and decrypt a vault document.
    Only the owner can download.
    """
    file_bytes, file_name = download_vault_document(
        db, doc_id, current_user.id
    )

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )


@router.post("/share/{doc_id}")
def create_share_link(
    doc_id: str,
    expire_hours: int = Query(24, description="Link expires after this many hours"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a time-limited share link.

    POST /api/vault/share/{doc_id}?expire_hours=48

    Anyone with the link can download within expire_hours.
    After that, link stops working automatically.
    """
    return generate_share_link(
        db, doc_id, current_user.id, expire_hours
    )


@router.get("/share/{token}")
def download_shared_document(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Download document via share token.
    No login required — public endpoint.
    Token must not be expired.
    """
    file_bytes, file_name = download_via_share_token(db, token)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )