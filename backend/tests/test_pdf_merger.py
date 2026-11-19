"""Tests for pdf_merger service."""

import os

from errors import ServiceResult
from services.pdf_merger import merge_pdfs


class TestMergePdfs:
    def test_missing_input_returns_failure(self, tmp_dir):
        """Non-existent file → failure."""
        result = merge_pdfs(
            [os.path.join(tmp_dir, "missing.pdf")],
            os.path.join(tmp_dir, "out.pdf"),
        )
        assert not result.success

    def test_empty_file_list_returns_failure(self, tmp_dir):
        """Empty file list → failure."""
        result = merge_pdfs([], os.path.join(tmp_dir, "out.pdf"))
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        """Always returns ServiceResult (not raw dict or exception)."""
        result = merge_pdfs([], os.path.join(tmp_dir, "out.pdf"))
        assert isinstance(result, ServiceResult)
        assert hasattr(result, "success")
        assert hasattr(result, "message")
