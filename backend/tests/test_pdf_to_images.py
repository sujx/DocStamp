"""PDF → images service: dpi bounds.

dpi is passed straight to `pdftoppm -r`, so an unbounded value turns a small
PDF into a multi-gigabyte bitmap allocation.  The bounds must be enforced
before the output directory is created and before pdftoppm is launched.
"""

import io
import os
from unittest.mock import patch

import pytest

from services.pdf_to_images import MAX_DPI, MIN_DPI, pdf_to_images


class TestDpiBounds:
    """Out-of-range resolutions are rejected, not passed to pdftoppm."""

    def test_dpi_above_max_is_rejected(self, tmp_path, sample_pdf_bytes):
        pdf = tmp_path / "src.pdf"
        pdf.write_bytes(sample_pdf_bytes)
        out = tmp_path / "out"

        with patch("services.pdf_to_images.subprocess.run") as run:
            result = pdf_to_images(str(pdf), str(out), fmt="png", dpi=MAX_DPI + 1)

        assert not result.success
        run.assert_not_called()
        assert not os.path.exists(out)

    def test_dpi_below_min_is_rejected(self, tmp_path, sample_pdf_bytes):
        pdf = tmp_path / "src.pdf"
        pdf.write_bytes(sample_pdf_bytes)
        out = tmp_path / "out"

        with patch("services.pdf_to_images.subprocess.run") as run:
            result = pdf_to_images(str(pdf), str(out), fmt="png", dpi=MIN_DPI - 1)

        assert not result.success
        run.assert_not_called()
        assert not os.path.exists(out)

    def test_absurd_dpi_is_rejected(self, tmp_path, sample_pdf_bytes):
        pdf = tmp_path / "src.pdf"
        pdf.write_bytes(sample_pdf_bytes)

        with patch("services.pdf_to_images.subprocess.run") as run:
            result = pdf_to_images(str(pdf), str(tmp_path / "out"), fmt="png", dpi=100000)

        assert not result.success
        run.assert_not_called()

    @pytest.mark.parametrize("dpi", [MIN_DPI, MAX_DPI, 200])
    def test_dpi_within_bounds_is_accepted(self, tmp_path, sample_pdf_bytes, dpi):
        pdf = tmp_path / "src.pdf"
        pdf.write_bytes(sample_pdf_bytes)
        out = tmp_path / "out"

        with patch("services.pdf_to_images.subprocess.run") as run:
            result = pdf_to_images(str(pdf), str(out), fmt="png", dpi=dpi)

        assert result.success, result.message
        run.assert_called_once()

    def test_bounds_are_the_documented_range(self):
        assert MIN_DPI == 72
        assert MAX_DPI == 600


class TestPdf2ImgEndpoint:
    """POST /api/v1/pdf2img — dpi arrives as a form field."""

    def test_out_of_range_dpi_returns_400(self, client, sample_pdf_bytes):
        resp = client.post(
            "/api/v1/pdf2img",
            data={
                "file": (io.BytesIO(sample_pdf_bytes), "src.pdf"),
                "format": "png",
                "dpi": "99999",
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_non_numeric_dpi_returns_400(self, client, sample_pdf_bytes):
        resp = client.post(
            "/api/v1/pdf2img",
            data={
                "file": (io.BytesIO(sample_pdf_bytes), "src.pdf"),
                "format": "png",
                "dpi": "abc",
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
