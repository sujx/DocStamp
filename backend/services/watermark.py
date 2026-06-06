"""Watermark addition and removal for Word and PDF files.

Supports:
- PDF: Watermark via overlay page created with reportlab
- DOCX: Watermark via header manipulation
- Removal: Clear DOCX headers; best-effort PDF watermark stripping
"""

import os
from io import BytesIO


def add_watermark(filepath: str, output_path: str, params: dict,
                  image_filepath: str = None) -> None:
    """Add a text or image watermark to a document.

    Args:
        filepath: Path to the source document (.docx or .pdf).
        output_path: Path to write the watermarked document.
        params: Watermark parameters dict:
            - watermark_type (str): "text" or "image", default "text"
            - text (str): Watermark text (for text type)
            - image (str): Base64 or path to image file (for image type)
            - font (str): Font name, default "Helvetica"
            - font_size (int): Font size in pt, default 48
            - color (str): Hex color, default "#D0D0D0"
            - opacity (float): 0.0-1.0, default 0.3
            - rotation (float): Degrees, default -45
            - position (str): "tile" or "center", default "tile"
            - spacing_x (int): Horizontal spacing for tile mode, default 200
            - spacing_y (int): Vertical spacing for tile mode, default 200
        image_filepath: Optional path to an uploaded image file for
                        image-type watermarks.

    Raises:
        ValueError: If the file format is unsupported or required params missing.
    """
    watermark_type = params.get("watermark_type", "text")

    if watermark_type == "text":
        text = params.get("text", "")
        if not text:
            raise ValueError("Watermark text is required")
    elif watermark_type == "image":
        if not image_filepath and not params.get("image"):
            raise ValueError("Watermark image is required")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        _watermark_pdf(filepath, output_path, params, image_filepath)
    elif ext == ".docx":
        _watermark_docx(filepath, output_path, params, image_filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _watermark_pdf(filepath: str, output_path: str, params: dict,
                   image_filepath: str = None) -> None:
    """Add watermark to a PDF file.

    Supports both text and image watermarks.
    """
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader

    watermark_type = params.get("watermark_type", "text")
    opacity = float(params.get("opacity", 0.3))
    opacity = max(0.0, min(1.0, opacity))
    rotation = float(params.get("rotation", -45))
    rotation = max(-180.0, min(180.0, rotation))
    position = params.get("position", "tile")
    spacing_x = int(params.get("spacing_x", 200))
    spacing_y = int(params.get("spacing_y", 200))

    reader = PdfReader(filepath)
    writer = PdfWriter()

    # Resolve image for image-type watermark
    watermark_img = None
    if watermark_type == "image":
        if image_filepath and os.path.isfile(image_filepath):
            watermark_img = ImageReader(image_filepath)
        elif params.get("image") and os.path.isfile(params["image"]):
            watermark_img = ImageReader(params["image"])

    if watermark_type == "text":
        text = params.get("text", "CONFIDENTIAL")
        font = params.get("font", "Helvetica")
        font_size = int(params.get("font_size", 48))
        color_hex = params.get("color", "#D0D0D0").lstrip("#")
        try:
            r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
        except (ValueError, IndexError):
            r, g, b = 208, 208, 208

    for page in reader.pages:
        mediabox = page.mediabox
        page_w = float(mediabox.width)
        page_h = float(mediabox.height)

        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_w, page_h))

        if watermark_type == "text":
            c.setFillColor(HexColor(f"#{r:02x}{g:02x}{b:02x}"))
            c.setFillAlpha(opacity)

            if position == "center":
                c.saveState()
                c.translate(page_w / 2, page_h / 2)
                c.rotate(rotation)
                c.setFont(font, font_size)
                text_width = c.stringWidth(text, font, font_size)
                c.drawString(-text_width / 2, -font_size / 2, text)
                c.restoreState()
            else:
                c.saveState()
                c.rotate(rotation)
                c.setFont(font, font_size)
                x_start = int(-page_w)
                x_end = int(page_w * 2)
                y_start = int(-page_h)
                y_end = int(page_h * 2)
                for y in range(y_start, y_end, spacing_y):
                    for x in range(x_start, x_end, spacing_x):
                        c.drawString(x, y, text)
                c.restoreState()

        elif watermark_type == "image" and watermark_img is not None:
            c.saveState()
            c.setFillAlpha(opacity)
            img_size = float(params.get("image_size", 150))  # pt

            if position == "center":
                img_w = min(img_size, page_w * 0.6)
                img_h = img_w  # aspect preserved by reportlab
                c.drawImage(
                    watermark_img,
                    (page_w - img_w) / 2, (page_h - img_h) / 2,
                    width=img_w, height=img_h,
                    preserveAspectRatio=True,
                )
            else:
                # Tiled image watermark
                img_w = min(img_size, spacing_x)
                img_h = img_w
                for y in range(0, int(page_h) + spacing_y, spacing_y):
                    for x in range(0, int(page_w) + spacing_x, spacing_x):
                        c.drawImage(
                            watermark_img,
                            x, y,
                            width=img_w, height=img_h,
                            preserveAspectRatio=True,
                        )

            c.restoreState()

        c.save()
        packet.seek(0)

        watermark_pdf_page = PdfReader(packet).pages[0]
        page.merge_page(watermark_pdf_page)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def _watermark_docx(filepath: str, output_path: str, params: dict,
                    image_filepath: str = None) -> None:
    """Add watermark to a DOCX file via header manipulation."""
    from docx import Document
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.shared import Pt, Inches, RGBColor

    watermark_type = params.get("watermark_type", "text")

    doc = Document(filepath)

    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        for paragraph in header.paragraphs:
            paragraph.clear()

        p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        if watermark_type == "text":
            text = params.get("text", "CONFIDENTIAL")
            font_size = int(params.get("font_size", 48))
            color_hex = params.get("color", "#D0D0D0").lstrip("#")
            try:
                r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
            except (ValueError, IndexError):
                r, g, b = 208, 208, 208

            run = p.add_run()
            run.text = text
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor(r, g, b)

        elif watermark_type == "image" and image_filepath and os.path.isfile(image_filepath):
            # Add image to header as watermark
            run = p.add_run()
            run.add_picture(image_filepath, width=Inches(3))
            # Center the image
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    doc.save(output_path)


def remove_watermark(filepath: str, output_path: str) -> dict:
    """Remove watermarks from a Word or PDF file.

    DOCX: Clears all header content across all sections (reliable).
    PDF: Attempts best-effort removal by stripping overlay content.
         Works best for PDFs watermarked by docStamp; results may vary
         for externally watermarked files.

    Args:
        filepath: Path to the source document (.docx or .pdf).
        output_path: Path to write the cleaned document.

    Returns:
        dict with keys: type ("docx" or "pdf"), method, warning (optional).

    Raises:
        ValueError: If the file format is unsupported.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".docx":
        return _remove_watermark_docx(filepath, output_path)
    elif ext == ".pdf":
        return _remove_watermark_pdf(filepath, output_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _remove_watermark_docx(filepath: str, output_path: str) -> dict:
    """Remove watermarks from DOCX by clearing all header content."""
    from docx import Document

    doc = Document(filepath)
    cleared = 0

    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        # Clear all paragraphs in the header
        for paragraph in header.paragraphs:
            if paragraph.text or paragraph.runs:
                paragraph.clear()
                cleared += 1

    doc.save(output_path)
    return {
        "type": "docx",
        "method": "header_cleared",
        "sections_cleared": cleared,
    }


def _remove_watermark_pdf(filepath: str, output_path: str) -> dict:
    """Attempt to remove watermarks from a PDF.

    Strategy (multi-layered, from least to most aggressive):
    1. Compress content streams — may merge fragmented overlay content.
    2. Delete /Annots — removes annotation-based watermarks.
    3. Delete /XObject — removes image-based watermark objects.

    Based on approach from https://github.com/jch0815/Python-PDF-
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(filepath)
    writer = PdfWriter()

    for page in reader.pages:
        # Strategy 1: compress content streams
        try:
            page.compress_content_streams()
        except (AttributeError, Exception):
            pass

        # Strategy 2: strip annotations (may contain watermark overlays)
        if "/Annots" in page:
            del page["/Annots"]

        # Strategy 3: strip XObjects (may contain watermark images)
        resources = page.get("/Resources", {})
        if "/XObject" in resources:
            del resources["/XObject"]

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "type": "pdf",
        "method": "content_compressed,annots_stripped,xobject_stripped",
        "warning": (
            "Removed annotations and XObject images from all pages. "
            "This may also affect legitimate stamps, comments, and embedded images. "
            "Results depend on how the watermark was added."
        ),
    }
