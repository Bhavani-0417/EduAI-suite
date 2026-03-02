import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings


def get_encryption_key() -> bytes:
    """
    Derive a consistent encryption key from SECRET_KEY.
    Uses PBKDF2 to turn any string into a valid Fernet key.
    
    Same SECRET_KEY always produces same encryption key —
    so files encrypted today can be decrypted tomorrow.
    """
    password = settings.SECRET_KEY.encode()
    salt = b"eduai_vault_salt_2024"

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_file(file_bytes: bytes) -> bytes:
    """
    Encrypt file bytes using Fernet (AES-128-CBC + HMAC).
    Returns encrypted bytes.
    
    Fernet = symmetric encryption — same key encrypts and decrypts.
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(file_bytes)
    return encrypted


def decrypt_file(encrypted_bytes: bytes) -> bytes:
    """
    Decrypt previously encrypted file bytes.
    Returns original file bytes.
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted