"""File upload security: size limits, extension whitelist, magic number verification.

Prevents:
- Overly large file uploads (DoS)
- Disallowed file extensions
- Extension-spoofed malicious files (e.g., .exe renamed to .pdf)
"""

import os
import struct

from errors import ErrorCode, ServiceError

# ── Extension Whitelist ─────────────────────────────────────────────────

ALLOWED_EXTENSIONS: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "csv": "text/csv",
    "md": "text/markdown",
    "markdown": "text/markdown",
    "txt": "text/plain",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# ── Magic Number Signatures ─────────────────────────────────────────────

# Maps file extension → expected leading bytes
# ZIP-based formats (docx/xlsx/pptx) share the PK signature
MAGIC_SIGNATURES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
    "pptx": b"PK\x03\x04",
}


# ── Public API ──────────────────────────────────────────────────────────

def validate_file_security(filepath: str, filename: str) -> None:
    """Comprehensive security validation for uploaded files.

    Runs three checks in order:
    1. File size ≤ MAX_FILE_SIZE (100 MB)
    2. Extension in ALLOWED_EXTENSIONS whitelist
    3. File header matches expected magic number signature

    Args:
        filepath: Full path to the uploaded file on disk.
        filename: Original filename (used for extension detection).

    Raises:
        ServiceError: On any validation failure, with the appropriate ErrorCode.
    """
    # 1. Size check
    _validate_size(filepath)

    # 2. Extension check
    ext = _extract_extension(filename)
    _validate_extension(ext)

    # 3. Magic number check
    _validate_magic(filepath, ext)


def _extract_extension(filename: str) -> str:
    """Get lowercase file extension without the dot."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _validate_size(filepath: str) -> None:
    """Check file does not exceed MAX_FILE_SIZE."""
    try:
        size = os.path.getsize(filepath)
    except OSError as e:
        raise ServiceError(ErrorCode.FILE_NOT_FOUND, f"Cannot read file: {e}")
    if size > MAX_FILE_SIZE:
        raise ServiceError(
            ErrorCode.FILE_TOO_LARGE,
            f"File size {_format_size(size)} exceeds limit of {_format_size(MAX_FILE_SIZE)}",
        )


def _validate_extension(ext: str) -> None:
    """Check file extension is in the whitelist."""
    if not ext:
        raise ServiceError(ErrorCode.UNSUPPORTED_FORMAT, "File has no extension")
    if ext not in ALLOWED_EXTENSIONS:
        raise ServiceError(
            ErrorCode.UNSUPPORTED_FORMAT,
            f"File extension .{ext} is not allowed",
        )


def _validate_magic(filepath: str, ext: str) -> None:
    """Check file header bytes match the expected magic number."""
    magic = MAGIC_SIGNATURES.get(ext)
    if magic is None:
        return  # No signature defined for this extension; skip check

    try:
        with open(filepath, "rb") as f:
            header = f.read(len(magic))
    except OSError as e:
        raise ServiceError(ErrorCode.FILE_NOT_FOUND, f"Cannot read file for magic check: {e}")

    if header != magic:
        raise ServiceError(
            ErrorCode.MAGIC_NUMBER_MISMATCH,
            f"File content does not match .{ext} format; upload rejected",
        )


# ── Helpers ─────────────────────────────────────────────────────────────

def _format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.0f} TB"
