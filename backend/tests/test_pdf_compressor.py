"""Tests for pdf_compressor service."""

import os

import pytest

from services.pdf_compressor import MAX_IMAGE_DIM, compress_pdf
from errors import ServiceResult

IMAGE_W, IMAGE_H = 2000, 1500


def _make_pdf_with_image(path: str) -> None:
    """Write a one-page PDF embedding a large, incompressible PNG."""
    from io import BytesIO

    from PIL import Image
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    img = Image.frombytes("RGB", (IMAGE_W, IMAGE_H), os.urandom(IMAGE_W * IMAGE_H * 3))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    c = canvas.Canvas(path, pagesize=(612, 792))
    c.drawImage(ImageReader(buf), 0, 0, width=612, height=792)
    c.showPage()
    c.save()


def _embedded_images(path: str) -> list:
    """Decode every image embedded in a PDF, failing loudly on corrupt streams."""
    from pypdf import PdfReader

    images = []
    for page in PdfReader(path).pages:
        for image_file in page.images:
            img = image_file.image
            img.load()
            images.append(img)
    return images


@pytest.fixture(scope="module")
def source_pdf(tmp_path_factory):
    """One large-image PDF shared by the module (generating it is slow)."""
    path = tmp_path_factory.mktemp("pdf") / "with_image.pdf"
    _make_pdf_with_image(str(path))
    return str(path)


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


class TestHighQualityImageDownsampling:
    """quality='high' rewrites embedded images — they must stay decodable."""

    def test_output_images_remain_decodable(self, source_pdf, tmp_dir):
        out = os.path.join(tmp_dir, "out.pdf")
        assert compress_pdf(source_pdf, out, quality="high").success

        images = _embedded_images(out)
        assert images, "compressed PDF lost all embedded images"

    def test_large_images_are_downsampled(self, source_pdf, tmp_dir):
        out = os.path.join(tmp_dir, "out.pdf")
        compress_pdf(source_pdf, out, quality="high")

        images = _embedded_images(out)
        assert max(max(img.size) for img in images) <= MAX_IMAGE_DIM

    def test_size_is_reduced(self, source_pdf, tmp_dir):
        out = os.path.join(tmp_dir, "out.pdf")
        result = compress_pdf(source_pdf, out, quality="high")

        assert result.data["compressed_size"] < result.data["original_size"]


class TestMediumQualityLeavesImagesAlone:
    def test_images_keep_original_dimensions(self, source_pdf, tmp_dir):
        out = os.path.join(tmp_dir, "out.pdf")
        compress_pdf(source_pdf, out, quality="medium")

        images = _embedded_images(out)
        assert images, "compressed PDF lost all embedded images"
        assert max(max(img.size) for img in images) == max(IMAGE_W, IMAGE_H)
