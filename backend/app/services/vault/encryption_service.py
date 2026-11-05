import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


def _derive_fernet_key(salt: bytes) -> bytes:
    """Derive a Fernet key from the configured master secret and a purpose-specific salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))


def get_encryption_key() -> bytes:
    """
    Return the original document-encryption key.

    IMPORTANT: Keep this salt, KDF, output length, and iteration count stable:
    previously encrypted vault files depend on this exact derivation.
    """
    return _derive_fernet_key(b"eduai_vault_salt_2024")


def get_ocr_encryption_key() -> bytes:
    """Use a separate key for OCR database fields (cryptographic domain separation)."""
    return _derive_fernet_key(b"eduai_vault_ocr_salt_v1")


def encrypt_file(file_bytes: bytes) -> bytes:
    """Encrypt document bytes with the legacy-compatible Fernet document key."""
    return Fernet(get_encryption_key()).encrypt(file_bytes)


def decrypt_file(encrypted_bytes: bytes) -> bytes:
    """Decrypt document bytes created by the existing vault encryption scheme."""
    return Fernet(get_encryption_key()).decrypt(encrypted_bytes)


OCR_CIPHERTEXT_PREFIX = "fernet:v1:"


def encrypt_ocr_text(plain_text: str | None) -> str | None:
    """Encrypt OCR text before placing it in the database."""
    if not plain_text:
        return None
    encrypted = Fernet(get_ocr_encryption_key()).encrypt(plain_text.encode("utf-8"))
    return OCR_CIPHERTEXT_PREFIX + encrypted.decode("ascii")


def decrypt_ocr_text(stored_text: str | None) -> str | None:
    """
    Decrypt versioned OCR ciphertext.

    Values without the prefix are legacy plaintext. Returning them unchanged
    allows old rows to remain readable until the explicit migration is run.
    """
    if stored_text is None:
        return None
    if not stored_text.startswith(OCR_CIPHERTEXT_PREFIX):
        return stored_text
    token = stored_text[len(OCR_CIPHERTEXT_PREFIX):].encode("ascii")
    return Fernet(get_ocr_encryption_key()).decrypt(token).decode("utf-8")


NOTES_CIPHERTEXT_PREFIX = "notes-fernet:v1:"


def get_notes_encryption_key() -> bytes:
    """Use a purpose-specific key for note content, distinct from vault keys."""
    return _derive_fernet_key(b"eduai_notes_content_salt_v1")


def encrypt_notes_text(plain_text: str | None) -> str | None:
    """Encrypt a note text value before persistence."""
    if not plain_text:
        return None
    encrypted = Fernet(get_notes_encryption_key()).encrypt(plain_text.encode("utf-8"))
    return NOTES_CIPHERTEXT_PREFIX + encrypted.decode("ascii")


def decrypt_notes_text(stored_text: str | None) -> str | None:
    """Decrypt versioned note text; preserve legacy plaintext during migration."""
    if stored_text is None:
        return None
    if not stored_text.startswith(NOTES_CIPHERTEXT_PREFIX):
        return stored_text
    token = stored_text[len(NOTES_CIPHERTEXT_PREFIX):].encode("ascii")
    return Fernet(get_notes_encryption_key()).decrypt(token).decode("utf-8")
