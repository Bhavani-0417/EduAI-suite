"""Encrypt legacy plaintext OCR fields in vault_documents.

Run from the backend directory with: python -m scripts.migrate_vault_ocr
Back up the database first. This migration leaves encrypted document blobs
untouched and does not change their existing Fernet key derivation.
"""
from app.db.database import SessionLocal
from app.models.vault import VaultDocument
from app.services.vault.encryption_service import (
    OCR_CIPHERTEXT_PREFIX,
    encrypt_ocr_text,
)


def main() -> None:
    db = SessionLocal()
    migrated = 0
    try:
        documents = db.query(VaultDocument).filter(
            VaultDocument.ocr_text.isnot(None)
        ).yield_per(100)
        for document in documents:
            if document.ocr_text and not document.ocr_text.startswith(OCR_CIPHERTEXT_PREFIX):
                document.ocr_text = encrypt_ocr_text(document.ocr_text)
                migrated += 1
                if migrated % 100 == 0:
                    db.commit()
        db.commit()
        print(f"Encrypted OCR text for {migrated} legacy vault document(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
