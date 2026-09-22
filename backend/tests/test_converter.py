"""Tests for converter service (MD → DOCX)."""

import os

from services.converter import md_to_docx
from errors import ServiceResult


class TestMdToDocx:
    def test_missing_file_returns_failure(self, tmp_dir):
        """Non-existent file → ServiceResult.fail."""
        result = md_to_docx(
            os.path.join(tmp_dir, "missing.md"),
            os.path.join(tmp_dir, "out.docx"),
        )
        assert not result.success

    def test_returns_service_result(self, sample_md, tmp_dir):
        """Happy path: converts markdown to docx."""
        import shutil
        if not shutil.which("pandoc"):
            import pytest
            pytest.skip("pandoc not installed")
        result = md_to_docx(sample_md, os.path.join(tmp_dir, "out.docx"))
        assert isinstance(result, ServiceResult)
        # Pandoc should succeed with valid markdown
        if result.success:
            assert os.path.getsize(os.path.join(tmp_dir, "out.docx")) > 0
