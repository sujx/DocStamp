"""Page decorator — add page numbers, headers, and footers to PDF pages."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from errors import ErrorCode, ServiceResult


def add_page_numbers(filepath: str, output_path: str, params: dict) -> ServiceResult[dict]:
    """Add page numbers, headers, or footers to a PDF.

    Params:
        mode: "page_number" / "header" / "footer"
        text: Format string — use {n} for current page, {total} for total pages
        position: "top-left" / "top-center" / "top-right" /
                  "bottom-left" / "bottom-center" / "bottom-right"
        font_size: Font size in pt (default 10)
        color: Hex color (default "#000000")
        start_number: Starting page number (default 1)
        margin: Distance from edge in pt (default 30)

    Args:
        filepath: Path to the source PDF.
        output_path: Path to write the decorated PDF.
        params: Dict with mode, text, position, font_size, color, start_number, margin.

    Returns:
        ServiceResult with dict: total_pages, decorated_pages.
    """
    mode = params.get("mode", "page_number")
    if mode not in ("page_number", "header", "footer"):
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Mode must be 'page_number', 'header', or 'footer'")

    text_template = params.get("text", "{n}" if mode == "page_number" else "")
    if not text_template:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, "Text template is required")

    position = params.get("position", "bottom-center")
    valid_positions = {"top-left", "top-center", "top-right",
                       "bottom-left", "bottom-center", "bottom-right"}
    if position not in valid_positions:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, f"Invalid position: {position}")

    font_size = int(params.get("font_size", 10))
    start_number = int(params.get("start_number", 1))
    margin = int(params.get("margin", 30))

    color_hex = params.get("color", "#000000").lstrip("#")
    try:
        r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
    except (ValueError, IndexError):
        r, g, b = 0, 0, 0

    try:
        reader = PdfReader(filepath)
    except Exception as e:
        return ServiceResult.fail(ErrorCode.PDF_READ_ERROR, f"Failed to read PDF: {e}")

    total = len(reader.pages)
    if total == 0:
        return ServiceResult.fail(ErrorCode.PDF_EMPTY, "PDF has no pages")

    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + start_number
        rendered_text = text_template.replace("{n}", str(page_num)).replace("{total}", str(total))

        mediabox = page.mediabox
        page_w = float(mediabox.width)
        page_h = float(mediabox.height)

        # Create overlay with the text
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_w, page_h))
        c.setFillColor(HexColor(f"#{r:02x}{g:02x}{b:02x}"))
        c.setFont("Helvetica", font_size)

        text_width = c.stringWidth(rendered_text, "Helvetica", font_size)
        text_height = font_size

        # Calculate position
        x, y = _text_position(page_w, page_h, text_width, text_height, position, margin)

        c.drawString(x, y, rendered_text)
        c.save()
        packet.seek(0)

        overlay = PdfReader(packet).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return ServiceResult.ok({"total_pages": total, "decorated_pages": total})


def _text_position(page_w: float, page_h: float, text_w: float, text_h: float,
                   position: str, margin: int) -> tuple[float, float]:
    """Calculate (x, y) coordinates for text placement."""
    horiz_map = {
        "left": margin,
        "center": (page_w - text_w) / 2,
        "right": page_w - text_w - margin,
    }
    vert_map = {
        "top": page_h - margin - text_h,
        "bottom": margin,
    }

    parts = position.split("-")
    v_key = parts[0]  # "top" or "bottom"
    h_key = parts[1]  # "left", "center", or "right"

    return horiz_map.get(h_key, margin), vert_map.get(v_key, margin)
