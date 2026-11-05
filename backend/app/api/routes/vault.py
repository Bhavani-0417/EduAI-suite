import io
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.middlewares.auth_middleware import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.vault.vault_service import (
    delete_vault_document,
    download_vault_document,
    download_via_share_token,
    generate_share_link,
    revoke_share_link,
    get_vault_documents,
    upload_vault_document,
)
from app.utils.vault_security import content_disposition_attachment

router = APIRouter(prefix="/api/vault", tags=["Document Vault"])


@router.post("/upload", status_code=201)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Query(
        "other",
        description="marksheet/certificate/transcript/id_card/offer_letter/other",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file; validate its signature and encrypt file and OCR contents."""
    doc = upload_vault_document(db, current_user.id, file, doc_type)
    return {
        "message": "Document encrypted and stored in vault!",
        "id": doc.id,
        "file_name": doc.file_name,
        "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else doc.doc_type,
        "has_ocr_text": bool(doc.ocr_text),
        "created_at": str(doc.created_at),
    }


@router.get("/")
def list_documents(
    doc_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List metadata for the authenticated student's vault documents."""
    docs = get_vault_documents(db, current_user.id, doc_type)
    return {
        "total": len(docs),
        "documents": [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else doc.doc_type,
                "has_ocr_text": bool(doc.ocr_text),
                "has_share_link": bool(doc.share_token),
                "created_at": str(doc.created_at),
            }
            for doc in docs
        ],
    }


@router.get("/download/{doc_id}")
def download_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a decrypted document owned by the authenticated user."""
    file_bytes, file_name = download_vault_document(db, doc_id, current_user.id)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": content_disposition_attachment(file_name),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/share/{doc_id}")
def create_share_link(
    doc_id: str,
    expire_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a public bearer link that expires between 1 and 168 hours."""
    return generate_share_link(db, doc_id, current_user.id, expire_hours)


@router.delete("/share/{doc_id}")
def revoke_document_share(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke any active public share token for an owned document."""
    revoke_share_link(db, doc_id, current_user.id)
    return {"message": "Share link revoked."}


@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a vault document owned by the authenticated user."""
    delete_vault_document(db, doc_id, current_user.id)
    return {"message": "Document deleted."}


@router.get("/share/{token}")
def download_shared_document(token: str, db: Session = Depends(get_db)):
    """Download a document using its expiring bearer token."""
    file_bytes, file_name = download_via_share_token(db, token)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": content_disposition_attachment(file_name),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
