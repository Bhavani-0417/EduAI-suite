import pytest

from app.utils.file_storage import resolve_generated_file, safe_filename_fragment


def test_safe_filename_fragment_removes_path_and_control_separators():
    fragment = safe_filename_fragment("../../a/b\\c\nResume")
    assert "/" not in fragment
    assert "\\" not in fragment
    assert "\n" not in fragment
    assert ".." not in fragment
    assert fragment


def test_resolve_generated_file_accepts_a_regular_file(tmp_path):
    output = tmp_path / "generated"
    output.mkdir()
    expected = output / "resume_123.pdf"
    expected.write_bytes(b"pdf")
    assert resolve_generated_file("resume_123.pdf", str(output)) == str(expected)


@pytest.mark.parametrize(
    "file_name",
    ["../secret.txt", "..\\secret.txt", "/etc/passwd", "", ".", "..", "folder/file.pdf"],
)
def test_resolve_generated_file_rejects_paths(tmp_path, file_name):
    with pytest.raises(ValueError):
        resolve_generated_file(file_name, str(tmp_path))


def test_resolve_generated_file_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_generated_file("missing.pdf", str(tmp_path))


def test_resolve_generated_file_rejects_symlink_escape(tmp_path):
    output = tmp_path / "generated"
    output.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    link = output / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment.")
    with pytest.raises(ValueError):
        resolve_generated_file("link.txt", str(output))
