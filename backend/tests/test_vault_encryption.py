import os

os.environ.setdefault("SECRET_KEY", "test-vault-master-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-vault-encryption.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-vault-jwt-secret")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-cloudinary-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-cloudinary-secret")

from app.services.vault.encryption_service import (
    OCR_CIPHERTEXT_PREFIX,
    decrypt_file,
    decrypt_ocr_text,
    encrypt_file,
    encrypt_ocr_text,
)


def test_existing_document_encryption_round_trips():
    payload = b"%PDF-1.7\\nexample"
    assert decrypt_file(encrypt_file(payload)) == payload


def test_ocr_text_is_encrypted_and_round_trips():
    plain_text = "Student name: Example Student; CGPA: 8.5"
    stored = encrypt_ocr_text(plain_text)
    assert stored.startswith(OCR_CIPHERTEXT_PREFIX)
    assert plain_text not in stored
    assert decrypt_ocr_text(stored) == plain_text


def test_ocr_decryption_preserves_legacy_plaintext_until_migration():
    assert decrypt_ocr_text("legacy OCR contents") == "legacy OCR contents"
    assert decrypt_ocr_text(None) is None
