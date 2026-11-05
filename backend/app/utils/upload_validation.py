"""Dependency-light validation helpers for encrypted vault uploads."""

from pathlib import PurePath

MAX_VAULT_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_VAULT_EXTENSIONS = frozenset({"pdf", "jpg", "jpeg", "png", "bmp"})


def validate_vault_upload(file_name: str | None, file_size: int) -> str:
    """Validate the user-supplied name/size and return a normalized extension."""
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


def validate_vault_file_content(extension: str, file_bytes: bytes) -> None:
    """
    Check file signatures before passing bytes to PDF/OCR parsers.

    This is a format sanity check, not malware scanning or a complete parser
    validation; the upload limit remains enforced separately.
    """
    if not isinstance(file_bytes, bytes) or not file_bytes:
        raise ValueError("The uploaded file must not be empty.")

    normalized = extension.lower().lstrip(".")
    signatures = {
        "png": file_bytes.startswith(b"\\x89PNG\\r\\n\\x1a\\n"),
        "jpg": file_bytes.startswith(b"\\xff\\xd8\\xff"),
        "jpeg": file_bytes.startswith(b"\\xff\\xd8\\xff"),
        "bmp": file_bytes.startswith(b"BM"),
        "pdf": b"%PDF-" in file_bytes[:1024],
    }
    if normalized not in signatures:
        raise ValueError("Unsupported vault file type.")
    if not signatures[normalized]:
        raise ValueError(
            f"The file contents do not match the .{normalized} extension."
        )
