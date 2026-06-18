"""Tests for properties service."""

import os

import pytest

from services.properties import read_properties, modify_properties
from errors import ServiceResult


class TestReadProperties:
    def test_missing_file_returns_failure(self, tmp_dir):
        """Non-existent file → ServiceResult.fail."""
        result = read_properties(os.path.join(tmp_dir, "missing.docx"))
        assert not result.success

    def test_txt_file_returns_failure(self, sample_txt):
        """Non-Office file → failure."""
        result = read_properties(sample_txt)
        assert not result.success


class TestModifyProperties:
    def test_missing_file_returns_failure(self, tmp_dir):
        """Non-existent file → failure."""
        result = modify_properties(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
            {"creator": "test"},
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        """Always returns ServiceResult."""
        result = modify_properties(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
            {},
        )
        assert isinstance(result, ServiceResult)
        assert hasattr(result, "success")
