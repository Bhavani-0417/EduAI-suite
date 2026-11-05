import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.fernet import InvalidToken
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.vault import DocumentType, VaultDocument
from app.services.notes.notes_service import extract_text
from app.services.vault.encryption_service import (
    encrypt_file,
    encrypt_ocr_text,
    decrypt_file,
)
from app.utils.upload_validation import (
    MAX_VAULT_UPLOAD_BYTES,
    validate_vault_file_content,
    validate_vault_upload,
)
from app.utils.vault_security import is_share_expired

logger = logging.getLogger(__name__)
OUTPUT_DIR = os.path.abspath("vault_files")


def _resolve_vault_path(stored_path: str) -> str:
    """Resolve a DB path and reject paths or symlinks outside the vault root."""
    vault_root = os.path.realpath(OUTPUT_DIR)
    resolved_path = os.path.realpath(stored_path)
    try:
        is_inside_vault = os.path.commonpath([vault_root, resolved_path]) == vault_root
    except ValueError:
        is_inside_vault = False
    if not is_inside_vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored document path is outside the vault directory.",
        )
    return resolved_path


def upload_vault_document(
    db: Session,
    student_id: str,
    file: UploadFile,
    doc_type: str,
) -> VaultDocument:
    """Validate, OCR, encrypt and persist a private vault document."""
    file_name = file.filename or ""
    file_bytes = file.file.read(MAX_VAULT_UPLOAD_BYTES + 1)

    if len(file_bytes) > MAX_VAULT_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Vault files must be 10 MB or smaller.",
        )

    try:
        extension = validate_vault_upload(file_name, len(file_bytes))
        validate_vault_file_content(extension, file_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    doc_type_map = {
        "marksheet": DocumentType.MARKSHEET,
        "certificate": DocumentType.CERTIFICATE,
        "transcript": DocumentType.TRANSCRIPT,
        "id_card": DocumentType.ID_CARD,
        "offer_letter": DocumentType.OFFER_LETTER,
        "other": DocumentType.OTHER,
    }
    normalized_doc_type = (doc_type or "").strip().lower()
    if normalized_doc_type not in doc_type_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document type.",
        )
    doc_type_enum = doc_type_map[normalized_doc_type]

    # Parser errors are handled by extract_text; original bytes remain encrypted.
    ocr_text = extract_text(file_bytes, extension)
    encrypted_bytes = encrypt_file(file_bytes)
    encrypted_ocr_text = encrypt_ocr_text(ocr_text[:3000] if ocr_text else None)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    encrypted_file_name = f"{student_id}_{uuid.uuid4()}.enc"
    encrypted_path = os.path.join(OUTPUT_DIR, encrypted_file_name)

    vault_doc = VaultDocument(
        id=str(uuid.uuid4()),
        student_id=student_id,
        doc_type=doc_type_enum,
        file_name=file_name,
        encrypted_url=encrypted_path,
        ocr_text=encrypted_ocr_text,
    )

    # Roll back DB work and remove the blob if persistence fails.
    try:
        with open(encrypted_path, "xb") as encrypted_file:
            encrypted_file.write(encrypted_bytes)
        db.add(vault_doc)
        db.commit()
    except Exception:
        db.rollback()
        try:
            os.remove(encrypted_path)
        except FileNotFoundError:
            pass
        except OSError:
            logger.exception("Failed to clean up encrypted vault upload after DB failure.")
        raise

    db.refresh(vault_doc)
    logger.info("Vault document stored: %s", vault_doc.id)
    return vault_doc


def get_vault_documents(
    db: Session,
    student_id: str,
    doc_type: str | None = None,
) -> list:
    """Get all vault documents for a student, optionally filtered by type."""
    query = db.query(VaultDocument).filter(VaultDocument.student_id == student_id)

    if doc_type:
        try:
            normalized_type = DocumentType(doc_type.strip().lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported document type.",
            ) from exc
        query = query.filter(VaultDocument.doc_type == normalized_type)

    return query.order_by(VaultDocument.created_at.desc()).all()


def _read_decrypted_document(doc: VaultDocument) -> bytes:
    encrypted_path = _resolve_vault_path(doc.encrypted_url)
    if not os.path.isfile(encrypted_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encrypted file missing. Please re-upload.",
        )
    try:
        with open(encrypted_path, "rb") as encrypted_file:
            return decrypt_file(encrypted_file.read())
    except InvalidToken as exc:
        logger.exception("Vault file could not be authenticated/decrypted.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The encrypted document could not be decrypted.",
        ) from exc
    except OSError as exc:
        logger.exception("Unable to read encrypted vault file.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encrypted file is unavailable.",
        ) from exc


def download_vault_document(
    db: Session,
    doc_id: str,
    student_id: str,
) -> tuple:
    """Decrypt and return a document belonging to the authenticated owner."""
    doc = db.query(VaultDocument).filter(
        VaultDocument.id == doc_id,
        VaultDocument.student_id == student_id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in vault.",
        )
    return _read_decrypted_document(doc), doc.file_name


def generate_share_link(
    db: Session,
    doc_id: str,
    student_id: str,
    expire_hours: int = 24,
) -> dict:
    """Generate a random bearer token with an explicit UTC expiry."""
    doc = db.query(VaultDocument).filter(
        VaultDocument.id == doc_id,
        VaultDocument.student_id == student_id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    doc.share_token = token
    doc.share_expires_at = expires_at
    db.commit()

    return {
        "share_token": token,
        "share_url": f"/api/vault/share/{token}",
        "expires_at": expires_at.isoformat(),
        "expires_in_hours": expire_hours,
    }


def download_via_share_token(db: Session, token: str) -> tuple:
    """Validate bearer token and expiry before returning decrypted bytes."""
    doc = db.query(VaultDocument).filter(
        VaultDocument.share_token == token,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid share link.",
        )

    if not doc.share_expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has no valid expiry and cannot be used.",
        )

    if is_share_expired(doc.share_expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired.",
        )

    return _read_decrypted_document(doc), doc.file_name


def delete_vault_document(
    db: Session,
    doc_id: str,
    student_id: str,
) -> None:
    """Delete an owned document and its encrypted file."""
    doc = db.query(VaultDocument).filter(
        VaultDocument.id == doc_id,
        VaultDocument.student_id == student_id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in vault.",
        )

    encrypted_path = _resolve_vault_path(doc.encrypted_url)
    db.delete(doc)
    db.commit()

    try:
        os.remove(encrypted_path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.exception(
            "Vault metadata was deleted, but encrypted file cleanup failed."
        )
