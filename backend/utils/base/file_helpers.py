"""Base utilities for file handling.

Mirrors the helpers originally inline in app.py for reuse across routes.
"""

import os
import uuid

from werkzeug.utils import secure_filename

from utils.file_security import validate_file_security


FORBIDDEN_PATH_CHARS = {"..", "/", "\\"}


def validate_filename(raw_name: str, allowed_exts: set) -> str:
    """Validate and sanitize a filename against an extension whitelist.

    Args:
        raw_name: Original filename from upload.
        allowed_exts: Set of allowed lowercase extensions (e.g. {"pdf", "docx"}).

    Returns:
        Sanitized filename.

    Raises:
        ValueError: If the filename is empty, contains forbidden characters,
                    or has a disallowed extension.
    """
    if not raw_name:
        raise ValueError("No filename provided")
    for char in FORBIDDEN_PATH_CHARS:
        if char in raw_name:
            raise ValueError("Invalid characters in filename")
    ext = raw_name.rsplit(".", 1)[-1].lower() if "." in raw_name else ""
    if ext not in allowed_exts:
        raise ValueError(f"File extension .{ext} is not allowed")
    filename = secure_filename(raw_name)
    if not filename:
        raise ValueError("Invalid filename after sanitization")
    if not filename.lower().endswith(f".{ext}"):
        filename = f"{filename}.{ext}"
    return filename


def save_upload(file, allowed_exts: set, upload_folder: str) -> tuple[str, str]:
    """Save an uploaded file with a unique prefix.

    Runs full security validation: extension whitelist → magic number → size limit.

    Args:
        file: Werkzeug FileStorage object.
        allowed_exts: Set of allowed extensions.
        upload_folder: Directory to save the file.

    Returns:
        (unique_name, filepath) tuple.
    """
    filename = validate_filename(file.filename, allowed_exts)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(upload_folder, unique_name)
    file.save(filepath)

    # Full security check: size, extension, magic number
    try:
        validate_file_security(filepath, file.filename)
    except ValueError:
        cleanup_files(filepath)
        raise

    return unique_name, filepath


def cleanup_files(*paths: str) -> None:
    """Remove files from disk, ignoring errors."""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
