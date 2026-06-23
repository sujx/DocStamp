"""PDF compression — reduce file size via content stream compression and image downsampling."""

import os
from io import BytesIO

from pypdf import PdfReader, PdfWriter

from errors import ErrorCode, ServiceResult


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

        if quality == "high":
            _compress_page_images(page)

        writer.add_page(page)

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
    """Downsample images in a PDF page to reduce file size."""
    try:
        from PIL import Image

        resources = page.get("/Resources", {})
        if "/XObject" not in resources:
            return

        xobjects = resources["/XObject"]
        for obj_name in list(xobjects.keys()):
            xobj = xobjects[obj_name]
            if xobj.get("/Subtype") != "/Image":
                continue

            try:
                data = xobj.get_data()
                img = Image.open(BytesIO(data))

                # Downsample large images
                w, h = img.size
                max_dim = 1200
                if w > max_dim or h > max_dim:
                    scale = max_dim / max(w, h)
                    new_size = (int(w * scale), int(h * scale))
                    img = img.resize(new_size, Image.LANCZOS)

                # Recompress as JPEG with moderate quality
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                buf = BytesIO()
                img.save(buf, format="JPEG", quality=60)
                buf.seek(0)

                # Replace image data
                compressed = Image.open(buf)
                xobj._data = buf.read()
            except Exception:
                pass  # Best-effort image compression
    except ImportError:
        pass
