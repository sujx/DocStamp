"""Shared fixtures for docStamp backend tests."""

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
    app = create_app()
    app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": tempfile.mkdtemp(prefix="docstamp_test_"),
    })
    return app


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
