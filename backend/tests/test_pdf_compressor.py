"""Tests for pdf_compressor service."""

import os

from services.pdf_compressor import compress_pdf
from errors import ServiceResult


class TestCompressPdf:
    def test_missing_file_returns_failure(self, tmp_dir):
        result = compress_pdf(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
            quality="medium",
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        result = compress_pdf(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
        )
        assert isinstance(result, ServiceResult)
