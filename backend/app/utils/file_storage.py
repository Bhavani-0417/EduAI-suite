"""Path-safe helpers for application-generated files."""

import os
import re


def safe_filename_fragment(value: str | None, max_length: int = 40) -> str:
    """Convert untrusted labels into a harmless filename component."""
    cleaned = re.sub(r"[^\w-]+", "_", str(value or ""), flags=re.UNICODE)
    cleaned = cleaned.strip("_-")[:max_length]
    return cleaned or "document"


def resolve_generated_file(file_name: str, output_dir: str = "generated_files") -> str:
    """Resolve a generated-file download by basename; reject traversal and symlink escapes."""
    if not isinstance(file_name, str) or not file_name:
        raise ValueError("Invalid file name.")
    if (
        "/" in file_name
        or "\\" in file_name
        or any(ord(char) < 32 or ord(char) == 127 for char in file_name)
        or file_name in {".", ".."}
    ):
        raise ValueError("Invalid file name.")

    root = os.path.realpath(output_dir)
    path = os.path.realpath(os.path.join(root, file_name))
    try:
        inside_root = os.path.commonpath([root, path]) == root
    except ValueError:
        inside_root = False
    if not inside_root or os.path.basename(path) != file_name:
        raise ValueError("Invalid file name.")
    if not os.path.isfile(path):
        raise FileNotFoundError(file_name)
    return path
