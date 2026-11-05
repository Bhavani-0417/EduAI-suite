"""Filename, size, and signature checks for personal learning-note uploads."""

from pathlib import PurePath

MAX_NOTE_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_NOTE_EXTENSIONS = frozenset({"pdf", "jpg", "jpeg", "png", "bmp", "tiff"})


def validate_note_upload(file_name: str | None, file_size: int) -> str:
    """Validate the upload metadata and return its normalized extension."""
    if not isinstance(file_name, str) or not file_name.strip():
        raise ValueError("A file name is required.")
    if "/" in file_name or "\\" in file_name:
        raise ValueError("The file name must not contain a directory path.")
    if len(file_name) > 255:
        raise ValueError("File names must be 255 characters or fewer.")
    if any(ord(char) < 32 or ord(char) == 127 for char in file_name):
        raise ValueError("File names must not contain control characters.")

    extension = PurePath(file_name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_NOTE_EXTENSIONS:
        raise ValueError("Only PDF, PNG, JPG/JPEG, BMP, and TIFF files are allowed.")
    if not isinstance(file_size, int) or file_size <= 0:
        raise ValueError("The uploaded file must not be empty.")
    if file_size > MAX_NOTE_UPLOAD_BYTES:
        raise ValueError("Note uploads must be 10 MB or smaller.")
    return extension


def validate_note_file_content(extension: str, file_bytes: bytes) -> None:
    """Check basic file signatures before sending content to OCR/PDF parsers."""
    if not isinstance(file_bytes, bytes) or not file_bytes:
        raise ValueError("The uploaded file must not be empty.")

    normalized = extension.lower().lstrip(".")
    signatures = {
        "pdf": b"%PDF-" in file_bytes[:1024],
        "png": file_bytes.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpg": file_bytes.startswith(b"\xff\xd8\xff"),
        "jpeg": file_bytes.startswith(b"\xff\xd8\xff"),
        "bmp": file_bytes.startswith(b"BM"),
        "tiff": file_bytes.startswith((b"II*\x00", b"MM\x00*")),
    }
    if normalized not in signatures:
        raise ValueError("Unsupported note file type.")
    if not signatures[normalized]:
        raise ValueError(
            f"The file contents do not match the .{normalized} extension."
        )
