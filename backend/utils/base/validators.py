"""Generic validators for filenames, paths, and MIME types.

Reusable across routes without Flask dependency.
"""

import os


def validate_extension(filename: str, allowed_exts: set) -> str:
    """Check file extension is in the allowed set. Returns the lowercased extension."""
    if not filename:
        raise ValueError("Empty filename")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not ext:
        raise ValueError("File has no extension")
    if ext not in allowed_exts:
        raise ValueError(f"Extension .{ext} is not allowed")
    return ext


def validate_path_safe(relative_path: str) -> bool:
    """Check a relative path contains no traversal sequences."""
    forbidden = {"..", "/", "\\"}
    return not any(c in relative_path for c in forbidden)


def ensure_dir(path: str, mode: int = 0o755) -> str:
    """Create directory if it doesn't exist. Returns the path."""
    os.makedirs(path, mode=mode, exist_ok=True)
    return path
