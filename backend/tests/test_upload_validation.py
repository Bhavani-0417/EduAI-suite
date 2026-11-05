import pytest

from app.utils.upload_validation import (
    ALLOWED_VAULT_EXTENSIONS,
    MAX_VAULT_UPLOAD_BYTES,
    validate_vault_file_content,
    validate_vault_upload,
)


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("transcript.pdf", "pdf"),
        ("Photo.JPG", "jpg"),
        ("scan.jpeg", "jpeg"),
        ("certificate.png", "png"),
        ("id-card.bmp", "bmp"),
    ],
)
def test_accepts_supported_extensions_case_insensitively(file_name, expected):
    assert validate_vault_upload(file_name, 1024) == expected


@pytest.mark.parametrize("file_name", ["", None, "   ", "notes.txt", "archive.pdf.exe"])
def test_rejects_missing_or_unsupported_names(file_name):
    with pytest.raises(ValueError):
        validate_vault_upload(file_name, 1024)


@pytest.mark.parametrize("file_name", ["../transcript.pdf", r"C:\Users\student\id.png"])
def test_rejects_path_components(file_name):
    with pytest.raises(ValueError, match="directory path"):
        validate_vault_upload(file_name, 1024)


@pytest.mark.parametrize("file_size", [0, -1])
def test_rejects_empty_or_negative_sizes(file_size):
    with pytest.raises(ValueError, match="must not be empty"):
        validate_vault_upload("scan.pdf", file_size)


def test_rejects_uploads_larger_than_ten_megabytes():
    with pytest.raises(ValueError, match="10 MB"):
        validate_vault_upload("scan.pdf", MAX_VAULT_UPLOAD_BYTES + 1)


@pytest.mark.parametrize(
    ("extension", "file_bytes"),
    [
        ("pdf", b"%PDF-1.7\nbody"),
        ("png", b"\x89PNG\r\n\x1a\nbody"),
        ("jpg", b"\xff\xd8\xffbody"),
        ("jpeg", b"\xff\xd8\xffbody"),
        ("bmp", b"BMbody"),
    ],
)
def test_accepts_matching_file_signatures(extension, file_bytes):
    validate_vault_file_content(extension, file_bytes)


@pytest.mark.parametrize(
    ("extension", "file_bytes"),
    [("pdf", b"not a pdf"), ("png", b"%PDF-1.7"), ("jpg", b"plain text")],
)
def test_rejects_content_with_wrong_extension_signature(extension, file_bytes):
    with pytest.raises(ValueError, match="contents do not match"):
        validate_vault_file_content(extension, file_bytes)


def test_allowed_extensions_are_the_documented_types():
    assert ALLOWED_VAULT_EXTENSIONS == {"pdf", "jpg", "jpeg", "png", "bmp"}
