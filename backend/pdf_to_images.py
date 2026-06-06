"""PDF page to image conversion using pdftoppm (poppler-utils)."""

import os
import subprocess
from typing import List, Optional


def pdf_to_images(
    filepath: str,
    output_dir: str,
    fmt: str = "png",
    dpi: int = 200,
    pages: Optional[List[int]] = None,
) -> dict:
    """Convert PDF pages to images.

    Args:
        filepath: Path to the source PDF.
        output_dir: Directory to write image files into.
        fmt: Output format — "png" or "jpeg".
        dpi: Output resolution in DPI (default 200).
        pages: 1-indexed list of pages to convert (None = all pages).

    Returns:
        dict with keys: total_pages, converted, files (list of filenames).
    """
    if not os.path.isfile(filepath):
        raise ValueError(f"File not found: {filepath}")

    os.makedirs(output_dir, exist_ok=True)

    # Validate format
    if fmt not in ("png", "jpeg"):
        raise ValueError(f"Unsupported format: {fmt}. Use 'png' or 'jpeg'.")

    # Get total page count
    from pypdf import PdfReader
    reader = PdfReader(filepath)
    total_pages = len(reader.pages)

    # Resolve page range
    if pages:
        for p in pages:
            if p < 1 or p > total_pages:
                raise ValueError(f"Page {p} out of range (1-{total_pages})")
        first_page = min(pages)
        last_page = max(pages)
    else:
        first_page = 1
        last_page = total_pages

    # pdftoppm outputs files like: prefix-1.png, prefix-2.png, ...
    # For jpeg: prefix-1.jpg, prefix-2.jpg
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
        raise RuntimeError(
            f"pdftoppm failed: {e.stderr.decode('utf-8', errors='replace')}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "pdftoppm not found. Install poppler-utils: apt install poppler-utils"
        )

    # Collect output files
    ext = "jpg" if fmt == "jpeg" else "png"
    files = sorted(
        [
            f for f in os.listdir(output_dir)
            if f.startswith("page-") and f.endswith(f".{ext}")
        ],
        key=lambda x: int(x.replace("page-", "").replace(f".{ext}", ""))
    )

    # If specific pages were requested, filter to only those pages
    if pages:
        requested = set(pages)
        files = [
            f for f in files
            if int(f.replace("page-", "").replace(f".{ext}", "")) in requested
        ]

    return {
        "total_pages": total_pages,
        "converted": len(files),
        "files": files,
        "dpi": dpi,
        "format": fmt,
    }
