"""Tests for watermark service."""

import os

from services.watermark import add_watermark, remove_watermark
from errors import ServiceResult


class TestAddWatermark:
    def test_missing_file_returns_failure(self, tmp_dir):
        result = add_watermark(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
            {"text": "CONFIDENTIAL"},
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        result = add_watermark(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
            {},
        )
        assert isinstance(result, ServiceResult)


class TestRemoveWatermark:
    def test_missing_file_returns_failure(self, tmp_dir):
        result = remove_watermark(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        result = remove_watermark(
            os.path.join(tmp_dir, "missing.pdf"),
            os.path.join(tmp_dir, "out.pdf"),
        )
        assert isinstance(result, ServiceResult)
