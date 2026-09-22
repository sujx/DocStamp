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
def sample_docx_bytes():
    """Minimal valid DOCX bytes (empty document)."""
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test content")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
