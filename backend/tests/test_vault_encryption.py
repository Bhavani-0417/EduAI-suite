import base64
import os

os.environ.setdefault("SECRET_KEY", "test-vault-master-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-vault-encryption.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-vault-jwt-secret")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-cloudinary-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-cloudinary-secret")

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.services.vault.encryption_service import (
    OCR_CIPHERTEXT_PREFIX,
    decrypt_file,
    decrypt_ocr_text,
    encrypt_file,
    encrypt_ocr_text,
)


def legacy_document_key(secret: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"eduai_vault_salt_2024",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def test_new_code_decrypts_documents_encrypted_with_the_original_key():
    payload = b"%PDF-1.7\nexample"
    old_ciphertext = Fernet(legacy_document_key(os.environ["SECRET_KEY"])).encrypt(payload)
    assert decrypt_file(old_ciphertext) == payload
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
