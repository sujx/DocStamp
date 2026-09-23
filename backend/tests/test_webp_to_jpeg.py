"""WebP → JPEG conversion.

Pillow is the real gate here: `MAGIC_SIGNATURES` has no webp entry, so a .webp
upload skips the magic-number check entirely and corrupt content must be caught
by the decoder instead.
"""

import io
import random

from PIL import Image

from services.webp_to_jpeg import webp_to_jpeg


class TestWebpToJpegService:
    def test_produces_a_jpeg(self, tmp_path, sample_webp_bytes):
        src = tmp_path / "in.webp"
        src.write_bytes(sample_webp_bytes)
        out = tmp_path / "out.jpg"

        result = webp_to_jpeg(str(src), str(out))

        assert result.success, result.message
        assert out.read_bytes()[:3] == b"\xff\xd8\xff"

    def test_alpha_is_composited_onto_white(self, tmp_path, sample_webp_rgba_bytes):
        src = tmp_path / "in.webp"
        src.write_bytes(sample_webp_rgba_bytes)
        out = tmp_path / "out.jpg"

        result = webp_to_jpeg(str(src), str(out))

        assert result.success, result.message
        with Image.open(out) as img:
            assert img.mode == "RGB"
            r, g, b = img.getpixel((0, 0))
        # 50% blue over a white backfill — red and green must be lifted well
        # above the pure-blue source value of 0.
        assert r > 100 and g > 100

    def test_lower_quality_produces_a_smaller_file(self, tmp_path):
        rng = random.Random(0)
        noisy = Image.new("RGB", (64, 64))
        noisy.putdata(
            [(rng.randrange(256), rng.randrange(256), rng.randrange(256))
             for _ in range(64 * 64)]
        )
        src = tmp_path / "in.webp"
        noisy.save(src, format="WEBP", lossless=True)

        hi, lo = tmp_path / "hi.jpg", tmp_path / "lo.jpg"
        assert webp_to_jpeg(str(src), str(hi), quality=95).success
        assert webp_to_jpeg(str(src), str(lo), quality=10).success

        assert lo.stat().st_size < hi.stat().st_size

    def test_animated_webp_uses_the_first_frame(self, tmp_path, sample_animated_webp_bytes):
        src = tmp_path / "anim.webp"
        src.write_bytes(sample_animated_webp_bytes)
        out = tmp_path / "out.jpg"

        assert webp_to_jpeg(str(src), str(out)).success

        with Image.open(out) as img:
            r, g, b = img.getpixel((0, 0))
        # Frame 1 is pure red; frames 2 and 3 are green and blue.
        assert r > 200 and g < 80 and b < 80

    def test_corrupt_webp_fails(self, tmp_path):
        src = tmp_path / "in.webp"
        src.write_bytes(b"not an image at all")

        result = webp_to_jpeg(str(src), str(tmp_path / "out.jpg"))

        assert not result.success

    def test_missing_file_fails(self, tmp_path):
        result = webp_to_jpeg(str(tmp_path / "nope.webp"), str(tmp_path / "out.jpg"))

        assert not result.success


class TestWebpToJpegEndpoint:
    URL = "/api/v1/webp-to-jpeg"

    def test_returns_a_jpeg(self, client, sample_webp_bytes):
        resp = client.post(
            self.URL,
            data={"file": (io.BytesIO(sample_webp_bytes), "photo.webp")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200
        assert resp.mimetype == "image/jpeg"
        assert resp.data[:3] == b"\xff\xd8\xff"

    def test_wrong_extension_returns_400(self, client, sample_webp_bytes):
        resp = client.post(
            self.URL,
            data={"file": (io.BytesIO(sample_webp_bytes), "photo.png")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400

    def test_corrupt_webp_returns_400(self, client):
        resp = client.post(
            self.URL,
            data={"file": (io.BytesIO(b"garbage bytes"), "photo.webp")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400

    def test_missing_file_returns_400(self, client):
        resp = client.post(self.URL, data={}, content_type="multipart/form-data")

        assert resp.status_code == 400


def test_module_is_registered_for_stats():
    """Missing from MODULE_NAMES → the tool never appears on /status."""
    from services.stats import MODULE_NAMES

    assert "webp-to-jpeg" in MODULE_NAMES
