"""Image to PDF merging with configurable page size and ordering.

Supports PNG, JPEG, TIFF input formats.
Uses img2pdf for lossless conversion.
"""

import os

import img2pdf
from PIL import Image

from errors import ErrorCode, ServiceResult


# Page size definitions in points (1 point = 1/72 inch)
PAGE_SIZES = {
    "a4": (595.28, 841.89),       # 210 × 297 mm
    "a4_landscape": (841.89, 595.28),
    "letter": (612, 792),          # 8.5 × 11 in
    "letter_landscape": (792, 612),
}


def images_to_pdf(
    image_paths: list,
    output_path: str,
    page_size: str = "original",
) -> ServiceResult[dict]:
    """Merge a list of images into a single PDF.

    Args:
        image_paths: Ordered list of image file paths.
        output_path: Path to write the output PDF.
        page_size: Page size preset — "original" keeps image dimensions,
                   "a4", "a4_landscape", "letter", "letter_landscape".

    Returns:
        ServiceResult with dict containing page_count and file_count.
    """
    if not image_paths:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "No images provided")

    # Validate all images exist and are readable
    for path in image_paths:
        if not os.path.isfile(path):
            return ServiceResult.fail(ErrorCode.FILE_NOT_FOUND, f"Image not found: {path}")
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception as e:
            return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Invalid or corrupt image: {path} ({e})")

    if page_size == "original":
        result = _merge_lossless(image_paths, output_path)
    else:
        result = _merge_with_page_size(image_paths, output_path, page_size)

    if not result.success:
        return result

    return ServiceResult.ok({"page_count": len(image_paths), "file_count": len(image_paths)})


def _merge_lossless(image_paths: list, output_path: str) -> ServiceResult[None]:
    """Merge images losslessly using img2pdf."""
    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        return ServiceResult.ok(None)
    except img2pdf.AlphaChannelError:
        # Some PNGs have alpha channels — convert to RGB first
        rgb_paths = []
        for path in image_paths:
            img = Image.open(path)
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                rgb_path = path.rsplit(".", 1)[0] + "_rgb.png"
                rgb_img.save(rgb_path, "PNG")
                rgb_paths.append(rgb_path)
            else:
                rgb_paths.append(path)

        try:
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(rgb_paths))
        except Exception as e:
            return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"Image to PDF conversion failed: {e}")
        finally:
            for p in rgb_paths:
                if p not in image_paths:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        return ServiceResult.ok(None)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"Image to PDF conversion failed: {e}")


def _merge_with_page_size(
    image_paths: list, output_path: str, page_size: str
) -> ServiceResult[None]:
    """Merge images into a PDF with each page set to a fixed size."""
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    size_map = {
        "a4": A4,
        "a4_landscape": (A4[1], A4[0]),
        "letter": LETTER,
        "letter_landscape": (LETTER[1], LETTER[0]),
    }

    page_w, page_h = size_map.get(page_size, A4)

    try:
        c = canvas.Canvas(output_path, pagesize=(page_w, page_h))

        for path in image_paths:
            img = Image.open(path)
            img_w, img_h = img.size

            margin = 20  # pt margin
            avail_w = page_w - 2 * margin
            avail_h = page_h - 2 * margin

            scale = min(avail_w / img_w, avail_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale

            x = (page_w - draw_w) / 2
            y = (page_h - draw_h) / 2

            c.drawImage(
                ImageReader(img),
                x, y,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True,
            )
            c.showPage()

        c.save()
        return ServiceResult.ok(None)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.CONVERSION_FAILED, f"Failed to create PDF: {e}")
