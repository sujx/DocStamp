"""Tests for metadata_cleaner service."""

import os

from services.metadata_cleaner import clean_metadata
from errors import ServiceResult


class TestCleanMetadata:
    def test_missing_file_returns_failure(self, tmp_dir):
        result = clean_metadata(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        result = clean_metadata(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
        )
        assert isinstance(result, ServiceResult)
