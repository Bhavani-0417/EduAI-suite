import os
import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from app.models.vault import VaultDocument, DocumentType
from app.services.vault.encryption_service import encrypt_file, decrypt_file
from app.services.notes.notes_service import extract_text

OUTPUT_DIR = "vault_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def upload_vault_document(
    db: Session,
    student_id: str,
    file: UploadFile,
    doc_type: str
) -> VaultDocument:
    """
    Upload and encrypt a document to the vault.

    Steps:
    1. Read file bytes
    2. Extract text with OCR (for searchability)
    3. Encrypt the entire file with AES
    4. Save encrypted file to disk
    5. Save metadata to PostgreSQL
    """

    file_bytes = file.file.read()
    file_name = file.filename
    extension = file_name.split(".")[-1].lower()

    allowed = ["pdf", "jpg", "jpeg", "png", "bmp"]
    if extension not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{extension} not allowed in vault."
        )

    # Step 1 — Extract text for OCR search
    print(f"📝 Extracting text from {file_name}...")
    ocr_text = extract_text(file_bytes, extension)

    # Step 2 — Encrypt file
    print(f"🔐 Encrypting {file_name}...")
    encrypted_bytes = encrypt_file(file_bytes)

    # Step 3 — Save encrypted file locally
    encrypted_file_name = f"{student_id}_{uuid.uuid4()}.enc"
    encrypted_path = os.path.join(OUTPUT_DIR, encrypted_file_name)

    with open(encrypted_path, "wb") as f:
        f.write(encrypted_bytes)

    # Step 4 — Map doc_type string to enum
    doc_type_map = {
        "marksheet": DocumentType.MARKSHEET,
        "certificate": DocumentType.CERTIFICATE,
        "transcript": DocumentType.TRANSCRIPT,
        "id_card": DocumentType.ID_CARD,
        "offer_letter": DocumentType.OFFER_LETTER,
        "other": DocumentType.OTHER,
    }

    doc_type_enum = doc_type_map.get(doc_type.lower(), DocumentType.OTHER)

    # Step 5 — Save metadata to DB
    vault_doc = VaultDocument(
        id=str(uuid.uuid4()),
        student_id=student_id,
        doc_type=doc_type_enum,
        file_name=file_name,
        encrypted_url=encrypted_path,
        ocr_text=ocr_text[:3000] if ocr_text else None
    )

    db.add(vault_doc)
    db.commit()
    db.refresh(vault_doc)

    print(f"✅ Vault document saved: {vault_doc.id}")
    return vault_doc


def get_vault_documents(
    db: Session,
    student_id: str,
    doc_type: str = None
) -> list:
    """Get all vault documents for a student"""
    query = db.query(VaultDocument).filter(
        VaultDocument.student_id == student_id
    )

    if doc_type:
        query = query.filter(
            VaultDocument.doc_type == doc_type
        )

    return query.order_by(VaultDocument.created_at.desc()).all()


def download_vault_document(
    db: Session,
    doc_id: str,
    student_id: str
) -> tuple:
    """
    Decrypt and return a vault document.
    Returns (file_bytes, file_name).
    """
    doc = db.query(VaultDocument).filter(
        VaultDocument.id == doc_id,
        VaultDocument.student_id == student_id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in vault."
        )

    if not os.path.exists(doc.encrypted_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encrypted file missing. Please re-upload."
        )

    # Read and decrypt
    with open(doc.encrypted_url, "rb") as f:
        encrypted_bytes = f.read()

    decrypted_bytes = decrypt_file(encrypted_bytes)
    return decrypted_bytes, doc.file_name


def generate_share_link(
    db: Session,
    doc_id: str,
    student_id: str,
    expire_hours: int = 24
) -> dict:
    """
    Generate a time-limited share token for a document.

    Token is a random string stored in DB.
    Anyone with the token can download within expire_hours.
    After that, token is invalid.
    """
    doc = db.query(VaultDocument).filter(
        VaultDocument.id == doc_id,
        VaultDocument.student_id == student_id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    # Generate secure random token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=expire_hours)

    doc.share_token = token
    doc.share_expires_at = expires_at

    db.commit()

    return {
        "share_token": token,
        "share_url": f"/api/vault/share/{token}",
        "expires_at": str(expires_at),
        "expires_in_hours": expire_hours
    }


def download_via_share_token(
    db: Session,
    token: str
) -> tuple:
    """
    Download a document using share token.
    Validates token and expiry before decrypting.
    """
    doc = db.query(VaultDocument).filter(
        VaultDocument.share_token == token
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid share link."
        )

    if doc.share_expires_at and datetime.utcnow() > doc.share_expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired."
        )

    with open(doc.encrypted_url, "rb") as f:
        encrypted_bytes = f.read()

    decrypted_bytes = decrypt_file(encrypted_bytes)
    return decrypted_bytes, doc.file_name