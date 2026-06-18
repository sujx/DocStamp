"""Tests for video_converter service."""

import os

import pytest

from services.video_converter import mp4_to_wmv


class TestMp4ToWmv:
    def test_no_ffmpeg_returns_failure(self, tmp_dir):
        """If ffmpeg is not installed, return TOOL_NOT_AVAILABLE."""
        import shutil
        if shutil.which("ffmpeg"):
            pytest.skip("ffmpeg is installed")
        result = mp4_to_wmv("nonexistent.mp4", os.path.join(tmp_dir, "out.wmv"))
        assert not result.success
        assert "not installed" in result.message.lower()

    def test_missing_input_returns_failure(self, tmp_dir):
        """Non-existent input file should fail."""
        import shutil
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not installed")
        result = mp4_to_wmv(
            os.path.join(tmp_dir, "missing.mp4"),
            os.path.join(tmp_dir, "out.wmv"),
        )
        assert not result.success

    def test_empty_file_returns_failure(self, tmp_dir):
        """An empty file is not a valid video."""
        import shutil
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not installed")
        input_path = os.path.join(tmp_dir, "empty.mp4")
        with open(input_path, "wb") as f:
            f.write(b"")
        result = mp4_to_wmv(input_path, os.path.join(tmp_dir, "out.wmv"))
        assert not result.success
