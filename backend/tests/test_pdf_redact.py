"""Tests for the PDF redaction service (services/pdf_redact.py)."""

import io
import os

import pytest
from PIL import Image, ImageChops, ImageFilter, ImageStat

from errors import ErrorCode, ServiceResult
from services.pdf_redact import (
    DEFAULT_MOSAIC_BLOCK,
    find_text_matches,
    inspect_pdf,
    mark_to_page_rect,
    pixelate,
    redact_pdf,
    region_text,
)


# ── helpers ─────────────────────────────────────────────────────────────

def _write(tmp_dir, name, data):
    path = os.path.join(tmp_dir, name)
    with open(path, "wb") as f:
        f.write(data)
    return path


def _mark_for(path, text, page_no=1):
    """Normalized top-left mark covering the first hit of `text` — what the UI sends."""
    import pymupdf

    doc = pymupdf.open(path)
    page = doc[page_no - 1]
    hits = page.search_for(text)
    assert hits, f"{text!r} not found on page {page_no}"
    r, pr = hits[0], page.rect
    mark = {
        "page": page_no,
        "x": (r.x0 - pr.x0) / pr.width,
        "y": (r.y0 - pr.y0) / pr.height,
        "w": r.width / pr.width,
        "h": r.height / pr.height,
    }
    doc.close()
    return mark


def _text_of(path, page_no=1):
    import pymupdf

    doc = pymupdf.open(path)
    text = doc[page_no - 1].get_text()
    doc.close()
    return text


def _render(path, page_no=1, dpi=72):
    import pymupdf

    doc = pymupdf.open(path)
    pix = doc[page_no - 1].get_pixmap(dpi=dpi)
    doc.close()
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def _edge_detail(img, box):
    return ImageStat.Stat(img.crop(box).convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]


# ── pixelate ────────────────────────────────────────────────────────────

class TestPixelate:
    def test_keeps_size_but_destroys_fine_detail(self):
        import random

        random.seed(3)
        src = Image.new("RGB", (64, 64))
        src.putdata([(random.randrange(256),) * 3 for _ in range(64 * 64)])

        out = pixelate(src, block=16)

        assert out.size == src.size
        assert _edge_detail(out, (0, 0, 64, 64)) < _edge_detail(src, (0, 0, 64, 64)) / 4

    def test_solid_image_is_unchanged(self):
        src = Image.new("RGB", (32, 32), (10, 20, 30))
        assert pixelate(src, block=8).tobytes() == src.tobytes()


# ── mark_to_page_rect ───────────────────────────────────────────────────

class TestMarkToPageRect:
    def test_maps_normalized_fractions_onto_page_points(self):
        import pymupdf

        page_rect = pymupdf.Rect(0, 0, 200, 400)
        rect = mark_to_page_rect({"page": 1, "x": 0.1, "y": 0.25, "w": 0.5, "h": 0.1}, page_rect)

        assert (rect.x0, rect.y0, rect.x1, rect.y1) == pytest.approx((20, 100, 120, 140))

    def test_respects_a_non_zero_page_origin(self):
        import pymupdf

        page_rect = pymupdf.Rect(10, 20, 210, 420)
        rect = mark_to_page_rect({"page": 1, "x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}, page_rect)

        assert (rect.x0, rect.y0) == pytest.approx((10, 20))

    def test_clamps_outside_the_page(self):
        import pymupdf

        page_rect = pymupdf.Rect(0, 0, 100, 100)
        rect = mark_to_page_rect({"page": 1, "x": -0.5, "y": -0.5, "w": 3.0, "h": 3.0}, page_rect)

        assert (rect.x0, rect.y0, rect.x1, rect.y1) == pytest.approx((0, 0, 100, 100))


# ── region_text (the verifier) ──────────────────────────────────────────

class TestRegionText:
    def test_finds_text_before_redaction(self, secret_pdf_bytes, tmp_dir):
        import pymupdf

        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        doc = pymupdf.open(src)
        page = doc[0]
        rect = page.search_for("SECRET-ID-1234")[0]

        assert "SECRET-ID-1234" in region_text(page, rect)
        doc.close()

    def test_finds_nothing_after_redaction(self, secret_pdf_bytes, tmp_dir):
        import pymupdf

        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")
        mark = _mark_for(src, "SECRET-ID-1234")
        redact_pdf(src, out, [mark])

        doc = pymupdf.open(out)
        page = doc[0]
        rect = mark_to_page_rect(mark, page.rect)

        assert region_text(page, rect).strip() == ""
        doc.close()


# ── inspect_pdf ─────────────────────────────────────────────────────────

class TestInspectPdf:
    def test_reports_page_count_and_sizes(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)

        result = inspect_pdf(src)

        assert result.success
        assert result.data["page_count"] == 1
        assert result.data["pages"][0]["width"] == pytest.approx(595.28, abs=0.5)
        assert result.data["pages"][0]["height"] == pytest.approx(841.89, abs=0.5)

    def test_rejects_an_encrypted_pdf(self, encrypted_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "enc.pdf", encrypted_pdf_bytes)

        result = inspect_pdf(src)

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR
        assert "encrypt" in result.message.lower()

    def test_rejects_more_pages_than_the_cap(self, multipage_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "multi.pdf", multipage_pdf_bytes)

        result = inspect_pdf(src, max_pages=2)

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR
        assert "2" in result.message

    def test_missing_file_fails(self, tmp_dir):
        result = inspect_pdf(os.path.join(tmp_dir, "nope.pdf"))

        assert not result.success
        assert result.error == ErrorCode.FILE_NOT_FOUND


# ── redact_pdf ──────────────────────────────────────────────────────────

class TestRedactPdf:
    def test_removes_text_inside_the_marked_region(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        result = redact_pdf(src, out, [_mark_for(src, "SECRET-ID-1234")])

        assert result.success, result.message
        assert "SECRET-ID-1234" not in _text_of(out)

    def test_keeps_text_outside_the_marked_region(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        redact_pdf(src, out, [_mark_for(src, "SECRET-ID-1234")])

        text = _text_of(out)
        assert "KEEP THIS LINE" in text
        assert "KEEP THIS TOO" in text

    def test_output_is_a_valid_pdf_with_the_same_page_count(self, multipage_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "m.pdf", multipage_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        result = redact_pdf(src, out, [_mark_for(src, "SECRET-2-9999", page_no=2)])

        assert result.success
        assert result.data["page_count"] == 3
        assert _text_of(out, 2).count("SECRET-2-9999") == 0

    def test_mosaic_is_applied_inside_the_region_only(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")
        mark = _mark_for(src, "SECRET-ID-1234")

        before = _render(src)
        redact_pdf(src, out, [mark])
        after = _render(out)
        diff = ImageChops.difference(before, after)
        bbox = diff.getbbox()
        assert bbox is not None, "the region was not modified at all"

        # change must stay in the top ~40% band where the secret line sits
        assert bbox[1] < before.height * 0.4
        assert _edge_detail(after, bbox) < _edge_detail(before, bbox)

    def test_marks_on_a_bitmap_page_are_reported_as_image_marks(self, scan_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "scan.pdf", scan_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        result = redact_pdf(src, out, [_mark_for(src, "OCR-SECRET-5678")])

        assert result.success, result.message
        assert result.data["image_marks"] == 1

    def test_invisible_ocr_text_in_the_region_is_removed(self, scan_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "scan.pdf", scan_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        redact_pdf(src, out, [_mark_for(src, "OCR-SECRET-5678")])

        assert "OCR-SECRET-5678" not in _text_of(out)

    def test_rotated_page_marks_land_on_the_right_place(self, rotated_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "rot.pdf", rotated_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")
        mark = _mark_for(src, "SECRET-ID-1234")

        result = redact_pdf(src, out, [mark])

        assert result.success, result.message
        text = _text_of(out)
        assert "SECRET-ID-1234" not in text
        assert "KEEP THIS LINE" in text

    def test_report_counts_marks_and_flags_nothing_left_over(self, multipage_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "m.pdf", multipage_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")
        marks = [_mark_for(src, f"SECRET-{i}-9999", page_no=i) for i in (1, 3)]

        result = redact_pdf(src, out, marks)

        assert result.data["total_marks"] == 2
        assert result.data["applied"] == 2
        assert result.data["leftover_regions"] == []
        assert result.data["image_marks"] == 0

    def test_no_marks_is_a_validation_error(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        result = redact_pdf(src, out, [])

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_out_of_range_page_is_a_validation_error(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        out = os.path.join(tmp_dir, "out.pdf")

        result = redact_pdf(src, out, [{"page": 9, "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1}])

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_missing_file_fails(self, tmp_dir):
        result = redact_pdf(os.path.join(tmp_dir, "nope.pdf"), os.path.join(tmp_dir, "o.pdf"), [
            {"page": 1, "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1}
        ])

        assert not result.success
        assert result.error == ErrorCode.FILE_NOT_FOUND

    def test_mosaic_block_size_is_honoured(self, secret_pdf_bytes, tmp_dir):
        src = _write(tmp_dir, "s.pdf", secret_pdf_bytes)
        coarse = os.path.join(tmp_dir, "coarse.pdf")
        fine = os.path.join(tmp_dir, "fine.pdf")
        mark = _mark_for(src, "SECRET-ID-1234")

        assert redact_pdf(src, coarse, [mark], mosaic_block=24).success
        assert redact_pdf(src, fine, [mark], mosaic_block=3).success

        box = ImageChops.difference(_render(src), _render(coarse)).getbbox()
        assert _edge_detail(_render(coarse), box) < _edge_detail(_render(fine), box)
        assert DEFAULT_MOSAIC_BLOCK > 0


# ── find_text_matches ───────────────────────────────────────────────────

class TestFindTextMatches:
    def test_literal_keyword_is_found(self, tmp_path, secret_pdf_bytes):
        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)

        result = find_text_matches(path, "SECRET-ID-1234")

        assert result.success, result.message
        matches = result.data["matches"]
        assert len(matches) == 1
        assert matches[0]["page"] == 1
        assert matches[0]["w"] > 0 and matches[0]["h"] > 0

    def test_matches_are_normalized_fractions(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, "SECRET")

        assert result.success, result.message
        for m in result.data["matches"]:
            assert 0 <= m["x"] < 1 and 0 <= m["y"] < 1
            assert 0 < m["w"] <= 1 and 0 < m["h"] <= 1

    def test_returned_box_covers_the_text_it_found(self, tmp_path, secret_pdf_bytes):
        import pymupdf

        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)
        mark = find_text_matches(path, "SECRET-ID-1234").data["matches"][0]

        doc = pymupdf.open(path)
        # Feeding the box back through mark_to_page_rect must land on the text,
        # which is what proves the normalization direction matches the UI's.
        assert "SECRET-ID-1234" in region_text(doc[0], mark_to_page_rect(mark, doc[0].rect))
        doc.close()

    def test_every_page_is_scanned(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, "KEEPER")

        assert [m["page"] for m in result.data["matches"]] == [1, 2, 3]

    def test_pages_filter_limits_the_scan(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, "KEEPER", pages=[2])

        assert [m["page"] for m in result.data["matches"]] == [2]

    def test_regex_pattern_matches_across_pages(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, r"SECRET-\d-9999", regex=True)

        assert result.success, result.message
        assert [m["page"] for m in result.data["matches"]] == [1, 2, 3]

    def test_regex_box_covers_the_whole_match(self, tmp_path, multipage_pdf_bytes):
        import pymupdf

        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)
        mark = find_text_matches(path, r"SECRET-\d-9999", regex=True, pages=[2]).data["matches"][0]

        doc = pymupdf.open(path)
        assert "SECRET-2-9999" in region_text(doc[1], mark_to_page_rect(mark, doc[1].rect))
        doc.close()

    def test_match_cap_truncates_instead_of_flooding(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, r"\d", regex=True, max_matches=3)

        assert result.success, result.message
        assert len(result.data["matches"]) == 3
        assert result.data["truncated"] is True

    def test_no_match_reports_empty_list(self, tmp_path, secret_pdf_bytes):
        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)

        result = find_text_matches(path, "NOT-IN-THIS-DOCUMENT")

        assert result.success, result.message
        assert result.data["matches"] == []
        assert result.data["truncated"] is False

    def test_page_without_a_text_layer_is_named(self, tmp_path, image_only_pdf_bytes):
        path = _write(str(tmp_path), "image-only.pdf", image_only_pdf_bytes)

        result = find_text_matches(path, "ANYTHING")

        assert result.success, result.message
        assert result.data["no_text_pages"] == [1]

    def test_text_pages_are_not_named_as_text_free(self, tmp_path, multipage_pdf_bytes):
        path = _write(str(tmp_path), "multi.pdf", multipage_pdf_bytes)

        result = find_text_matches(path, "ANYTHING")

        assert result.data["no_text_pages"] == []

    def test_invisible_ocr_text_still_counts_as_searchable(self, tmp_path, scan_pdf_bytes):
        """A scan with an OCR layer is searchable, so it is not reported as text-free."""
        path = _write(str(tmp_path), "scan.pdf", scan_pdf_bytes)

        result = find_text_matches(path, "OCR-SECRET-5678")

        assert result.data["no_text_pages"] == []
        assert len(result.data["matches"]) == 1

    def test_empty_pattern_fails(self, tmp_path, secret_pdf_bytes):
        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)

        result = find_text_matches(path, "   ")

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_invalid_regex_fails(self, tmp_path, secret_pdf_bytes):
        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)

        result = find_text_matches(path, "SECRET-(\\d", regex=True)

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_missing_file_fails(self, tmp_dir):
        result = find_text_matches(os.path.join(tmp_dir, "nope.pdf"), "SECRET")

        assert not result.success
        assert result.error == ErrorCode.FILE_NOT_FOUND

    def test_encrypted_pdf_is_rejected(self, tmp_path, encrypted_pdf_bytes):
        path = _write(str(tmp_path), "locked.pdf", encrypted_pdf_bytes)

        result = find_text_matches(path, "SECRET")

        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_out_of_range_page_fails(self, tmp_path, secret_pdf_bytes):
        path = _write(str(tmp_path), "secret.pdf", secret_pdf_bytes)

        result = find_text_matches(path, "SECRET", pages=[7])

        assert not result.success
        assert result.error == ErrorCode.PDF_PAGE_OUT_OF_RANGE
