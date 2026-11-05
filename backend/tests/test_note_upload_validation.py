import pytest

from app.utils.note_upload_validation import (
    ALLOWED_NOTE_EXTENSIONS,
    MAX_NOTE_UPLOAD_BYTES,
    validate_note_file_content,
    validate_note_upload,
)


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("notes.pdf", "pdf"),
        ("scan.PNG", "png"),
        ("photo.JPG", "jpg"),
        ("image.jpeg", "jpeg"),
        ("scan.bmp", "bmp"),
        ("archive.tiff", "tiff"),
    ],
)
def test_accepts_supported_note_extensions(file_name, expected):
    assert validate_note_upload(file_name, 100) == expected


@pytest.mark.parametrize(
    "file_name",
    ["", None, "  ", "../notes.pdf", r"C:\Users\student\notes.pdf", "notes.exe"],
)
def test_rejects_invalid_note_filenames(file_name):
    with pytest.raises(ValueError):
        validate_note_upload(file_name, 100)


@pytest.mark.parametrize("file_name", ["a" * 256 + ".pdf", "bad\nname.pdf"])
def test_rejects_long_or_control_character_note_filenames(file_name):
    with pytest.raises(ValueError):
        validate_note_upload(file_name, 100)


@pytest.mark.parametrize("file_size", [0, -1, MAX_NOTE_UPLOAD_BYTES + 1])
def test_rejects_invalid_note_sizes(file_size):
    with pytest.raises(ValueError):
        validate_note_upload("notes.pdf", file_size)


@pytest.mark.parametrize(
    ("extension", "content"),
    [
        ("pdf", b"%PDF-1.7\nbody"),
        ("png", b"\x89PNG\r\n\x1a\nbody"),
        ("jpg", b"\xff\xd8\xffbody"),
        ("jpeg", b"\xff\xd8\xffbody"),
        ("bmp", b"BMbody"),
        ("tiff", b"II*\x00body"),
    ],
)
def test_accepts_matching_note_signatures(extension, content):
    validate_note_file_content(extension, content)


@pytest.mark.parametrize(
    ("extension", "content"),
    [("pdf", b"not a pdf"), ("png", b"%PDF-1.7"), ("tiff", b"plain text")],
)
def test_rejects_note_content_with_wrong_signature(extension, content):
    with pytest.raises(ValueError, match="contents do not match"):
        validate_note_file_content(extension, content)


def test_allowed_note_extensions_match_supported_extractors():
    assert ALLOWED_NOTE_EXTENSIONS == {"pdf", "jpg", "jpeg", "png", "bmp", "tiff"}
