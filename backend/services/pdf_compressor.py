"""PDF compression — reduce file size via content stream compression and image downsampling."""

import os

from pypdf import PdfReader, PdfWriter

from errors import ErrorCode, ServiceResult

MAX_IMAGE_DIM = 1200


def compress_pdf(filepath: str, output_path: str, quality: str = "medium") -> ServiceResult[dict]:
    """Compress a PDF file (low/medium/high)."""
    if not os.path.isfile(filepath):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Input file not found")
    if quality not in ("low", "medium", "high"):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Quality must be 'low', 'medium', or 'high'")

    original_size = os.path.getsize(filepath)

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    writer = PdfWriter()

    # Strip metadata
    writer._info = None
    if hasattr(writer, '_metadata'):
        writer._metadata = None

    for page in reader.pages:
        if quality in ("medium", "high"):
            try:
                page.compress_content_streams()
            except (AttributeError, Exception):
                pass

        writer.add_page(page)

    if quality == "high":
        # Must run on writer-owned pages — ImageFile.replace() rejects images
        # that still belong to a PdfReader.
        for page in writer.pages:
            _compress_page_images(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    compressed_size = os.path.getsize(output_path)
    ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0.0

    return ServiceResult.ok({
        "original_size": original_size,
        "compressed_size": compressed_size,
        "ratio": ratio,
    })


def _compress_page_images(page) -> None:
    """Downsample oversized images in a writer-owned page and re-encode them as JPEG.

    Images already within MAX_IMAGE_DIM are left untouched.
    """
    try:
        from PIL import Image
    except ImportError:
        return

    for image_file in list(page.images):
        try:
            img = image_file.image
            w, h = img.size
            if max(w, h) <= MAX_IMAGE_DIM:
                continue

            scale = MAX_IMAGE_DIM / max(w, h)
            resized = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            if resized.mode not in ("RGB", "L"):
                resized = resized.convert("RGB")

            image_file.replace(resized, quality=60)
        except Exception:
            pass  # Best-effort image compression
