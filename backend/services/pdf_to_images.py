"""PDF page to image conversion using pdftoppm (poppler-utils)."""

import os
import subprocess
from typing import Optional

from pypdf import PdfReader

from errors import ErrorCode, ServiceResult

MIN_DPI = 72
MAX_DPI = 600


def pdf_to_images(
    filepath: str,
    output_dir: str,
    fmt: str = "png",
    dpi: int = 200,
    pages: Optional[list[int]] = None,
) -> ServiceResult[dict]:
    """Convert PDF pages to images.

    Args:
        filepath: Path to the source PDF.
        output_dir: Directory to write image files into.
        fmt: Output format — "png" or "jpeg".
        dpi: Output resolution in DPI (MIN_DPI–MAX_DPI).
        pages: 1-indexed list of pages to convert (None = all pages).

    Returns:
        ServiceResult with dict keys: total_pages, converted, files, dpi, format.
    """
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"File not found: {filepath}")

    if fmt not in ("png", "jpeg"):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Unsupported format: {fmt}. Use 'png' or 'jpeg'.")

    # pdftoppm allocates width*height*4 bytes per page, so an unbounded dpi turns
    # a single page into a multi-gigabyte bitmap.  Reject before touching disk.
    try:
        dpi = int(dpi)
    except (TypeError, ValueError):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Invalid DPI: {dpi!r}")
    if not MIN_DPI <= dpi <= MAX_DPI:
        return ServiceResult.fail(
            ErrorCode.VALIDATION_ERROR,
            f"DPI must be between {MIN_DPI} and {MAX_DPI}, got {dpi}",
        )

    os.makedirs(output_dir, exist_ok=True)

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    total_pages = len(reader.pages)

    # Resolve page range
    if pages:
        for p in pages:
            if p < 1 or p > total_pages:
                return ServiceResult.fail(
                    ErrorCode.PDF_PAGE_OUT_OF_RANGE,
                    f"Page {p} out of range (1-{total_pages})",
                )
        first_page = min(pages)
        last_page = max(pages)
    else:
        first_page = 1
        last_page = total_pages

    prefix = os.path.join(output_dir, "page")

    cmd = [
        "pdftoppm",
        f"-{fmt}",
        "-r", str(dpi),
        "-f", str(first_page),
        "-l", str(last_page),
        filepath,
        prefix,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except subprocess.CalledProcessError as e:
        return ServiceResult.fail(
            ErrorCode.CONVERSION_FAILED,
            f"pdftoppm failed: {e.stderr.decode('utf-8', errors='replace')}",
        )
    except FileNotFoundError:
        return ServiceResult.fail(
            ErrorCode.TOOL_NOT_AVAILABLE,
            "pdftoppm not found. Install poppler-utils: apt install poppler-utils",
        )

    # Collect output files
    ext = "jpg" if fmt == "jpeg" else "png"
    files = sorted(
        [
            f for f in os.listdir(output_dir)
            if f.startswith("page-") and f.endswith(f".{ext}")
        ],
        key=lambda x: int(x.replace("page-", "").replace(f".{ext}", "")),
    )

    if pages:
        requested = set(pages)
        files = [
            f for f in files
            if int(f.replace("page-", "").replace(f".{ext}", "")) in requested
        ]

    return ServiceResult.ok({
        "total_pages": total_pages,
        "converted": len(files),
        "files": files,
        "dpi": dpi,
        "format": fmt,
    })
