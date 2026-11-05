"""Small, dependency-free validation helpers for vault uploads."""

from pathlib import PurePath

MAX_VAULT_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_VAULT_EXTENSIONS = frozenset({"pdf", "jpg", "jpeg", "png", "bmp"})


def validate_vault_upload(file_name: str | None, file_size: int) -> str:
    """Validate a vault upload and return its lower-case extension."""
    if not isinstance(file_name, str) or not file_name.strip():
        raise ValueError("A file name is required.")
    if "/" in file_name or "\\" in file_name:
        raise ValueError("The file name must not contain a directory path.")

    extension = PurePath(file_name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_VAULT_EXTENSIONS:
        raise ValueError("Only PDF, PNG, JPG/JPEG, and BMP files are allowed.")
    if not isinstance(file_size, int) or file_size <= 0:
        raise ValueError("The uploaded file must not be empty.")
    if file_size > MAX_VAULT_UPLOAD_BYTES:
        raise ValueError("Vault files must be 10 MB or smaller.")
    return extension
