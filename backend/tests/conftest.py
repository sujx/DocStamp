"""Shared fixtures for docStamp backend tests."""

import io
import os
import sys
import tempfile

import pytest

# Ensure backend/ is on sys.path so 'from services.xxx' works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


@pytest.fixture
def app():
    """Flask app with test config."""
    test_upload = tempfile.mkdtemp(prefix="docstamp_test_")
    app = create_app()
    app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": test_upload,
    })
    from config import Config
    original = Config.UPLOAD_FOLDER
    Config.UPLOAD_FOLDER = test_upload
    yield app
    Config.UPLOAD_FOLDER = original


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def tmp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory(prefix="docstamp_test_") as d:
        yield d


@pytest.fixture
def sample_txt(tmp_dir):
    """Create a small text file for testing."""
    path = os.path.join(tmp_dir, "sample.txt")
    with open(path, "w") as f:
        f.write("Hello World\nThis is a test.\n")
    return path


@pytest.fixture
def sample_md(tmp_dir):
    """Create a small markdown file for testing."""
    path = os.path.join(tmp_dir, "sample.md")
    with open(path, "w") as f:
        f.write("# 测试文档\n\n这是正文内容。\n\n## 第二节\n\n- 列表项1\n- 列表项2\n")
    return path


@pytest.fixture
def sample_pdf_bytes():
    """Minimal valid PDF bytes (1-page empty PDF)."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n"
    )


@pytest.fixture
def sample_pdf_file(sample_pdf_bytes):
    """File-like object containing a minimal PDF."""
    return io.BytesIO(sample_pdf_bytes)


@pytest.fixture
def sample_webp_bytes():
    """2×2 opaque WebP, generated in memory."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (2, 2), (200, 30, 40)).save(buf, format="WEBP")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_webp_rgba_bytes():
    """2×2 WebP with an alpha channel — exercises the white-composite path."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGBA", (2, 2), (0, 0, 255, 128)).save(buf, format="WEBP")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_animated_webp_bytes():
    """3-frame WebP: red, green, blue — first frame must be the one converted."""
    from PIL import Image
    frames = [Image.new("RGB", (8, 8), c) for c in ((255, 0, 0), (0, 255, 0), (0, 0, 255))]
    buf = io.BytesIO()
    frames[0].save(buf, format="WEBP", save_all=True, append_images=frames[1:],
                   duration=100, loop=0)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_docx_bytes():
    """Minimal valid DOCX bytes (empty document)."""
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test content")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ── PDF redaction fixtures ──────────────────────────────────────────────

@pytest.fixture
def secret_pdf_bytes():
    """1-page A4, bottom-up: keeper line, secret line, keeper line."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, h = A4
    c.setFont("Helvetica", 14)
    c.drawString(72, h - 100, "KEEP THIS LINE")
    c.drawString(72, h - 130, "SECRET-ID-1234")
    c.drawString(72, h - 160, "KEEP THIS TOO")
    c.save()
    buf.seek(0)
    return buf.read()


@pytest.fixture
def multipage_pdf_bytes():
    """3-page A4, one secret line per page."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, h = A4
    for i in range(3):
        c.setFont("Helvetica", 14)
        c.drawString(72, h - 100, f"PAGE {i + 1} KEEPER")
        c.drawString(72, h - 130, f"SECRET-{i + 1}-9999")
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@pytest.fixture
def scan_pdf_bytes():
    """1-page PDF whose visible content is a bitmap, plus an invisible OCR text layer.

    Stands in for a scanned document: no visible text objects, but an OCR layer
    that must not survive redaction.
    """
    import random

    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    random.seed(7)
    img = Image.new("RGB", (600, 600))
    img.putdata([(random.randrange(120, 200),) * 3 for _ in range(600 * 600)])
    ibuf = io.BytesIO()
    img.save(ibuf, format="PNG")
    ibuf.seek(0)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, h = A4
    c.drawImage(ImageReader(ibuf), 72, h - 672, width=451, height=564)
    ocr = c.beginText(100, h - 300)
    ocr.setFont("Helvetica", 14)
    ocr.setTextRenderMode(3)  # invisible — an OCR layer, not visible text
    ocr.textLine("OCR-SECRET-5678")
    c.drawText(ocr)
    c.save()
    buf.seek(0)
    return buf.read()


@pytest.fixture
def image_only_pdf_bytes():
    """1-page PDF that is nothing but a bitmap — no text objects of any kind.

    The scan fixture above still carries an extractable OCR layer; this one is
    what keyword search genuinely cannot help with.
    """
    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    img = Image.new("RGB", (600, 600), (180, 180, 180))
    ibuf = io.BytesIO()
    img.save(ibuf, format="PNG")
    ibuf.seek(0)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, h = A4
    c.drawImage(ImageReader(ibuf), 72, h - 672, width=451, height=564)
    c.save()
    buf.seek(0)
    return buf.read()


@pytest.fixture
def rotated_pdf_bytes(secret_pdf_bytes):
    """The secret PDF with every page rotated 90° — marks must still land right."""
    import io as _io

    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(_io.BytesIO(secret_pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(90)
        writer.add_page(page)
    buf = _io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def encrypted_pdf_bytes(secret_pdf_bytes):
    """The secret PDF behind a user password."""
    import io as _io

    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(_io.BytesIO(secret_pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("hunter2")
    buf = _io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()

