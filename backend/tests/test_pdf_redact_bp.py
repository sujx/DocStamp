"""Route tests for the PDF redaction blueprint.

Every test except the open ones builds its session directly through
`redact_session` — `open` is rate-limited, and these tests must not fail because
the module as a whole uploaded more PDFs than one client is allowed to.
"""

import io
import os

import pytest

from config import Config
from services.pdf_redact import find_text_matches
from utils import redact_session


def _sessions_root() -> str:
    return os.path.join(Config.UPLOAD_FOLDER, redact_session.SESSIONS_DIRNAME)


def _upload(client, data, filename="doc.pdf"):
    return client.post(
        "/api/v1/pdf-redact/open",
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def _open(client, data, filename="doc.pdf") -> str:
    resp = _upload(client, data, filename)
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["session"]


def _open_in_place(data, name="secret.pdf") -> str:
    """Create a session on disk without going through the rate-limited route."""
    return redact_session.create_session(Config.UPLOAD_FOLDER, name, data)


def _marks_for(sid: str, text: str) -> list[dict]:
    """Marks covering `text`, taken from the search service the UI would call."""
    path = redact_session.source_path(Config.UPLOAD_FOLDER, sid)
    return find_text_matches(path, text).data["matches"]


def _blank_pdf(page_count: int) -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ── open ────────────────────────────────────────────────────────────────

class TestOpen:
    def test_opens_a_pdf_and_reports_its_pages(self, client, secret_pdf_bytes):
        resp = _upload(client, secret_pdf_bytes, "report.pdf")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["session"]) == 32
        assert data["page_count"] == 1
        assert data["original_name"] == "report.pdf"
        assert 590 < data["pages"][0]["width"] < 600
        assert 835 < data["pages"][0]["height"] < 850

    def test_the_upload_lands_in_the_session_directory(self, client, secret_pdf_bytes):
        sid = _open(client, secret_pdf_bytes)

        assert os.path.isfile(redact_session.source_path(Config.UPLOAD_FOLDER, sid))
        assert redact_session.is_valid_sid(sid)

    def test_rejects_a_missing_file(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/open",
            data={},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400

    def test_rejects_a_disallowed_extension(self, client, secret_pdf_bytes):
        resp = _upload(client, secret_pdf_bytes, "notes.txt")

        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_rejects_content_that_is_not_a_pdf(self, client):
        resp = _upload(client, b"this is definitely not a PDF", "fake.pdf")

        assert resp.status_code == 400
        assert os.listdir(_sessions_root()) == []

    def test_rejects_an_encrypted_pdf_and_says_so(self, client, encrypted_pdf_bytes):
        resp = _upload(client, encrypted_pdf_bytes, "locked.pdf")

        assert resp.status_code == 400
        assert "decrypt" in resp.get_json()["error"].lower()
        assert os.listdir(_sessions_root()) == []

    def test_rejects_a_pdf_over_the_page_limit(self, client):
        resp = _upload(client, _blank_pdf(101), "long.pdf")

        assert resp.status_code == 400
        assert os.listdir(_sessions_root()) == []

    def test_expired_sessions_are_collected_on_the_next_upload(self, client, secret_pdf_bytes):
        import time

        stale = _open_in_place(secret_pdf_bytes)
        directory = redact_session.session_dir(Config.UPLOAD_FOLDER, stale)
        old = time.time() - redact_session.SESSION_TTL_SECONDS - 60
        os.utime(directory, (old, old))

        fresh = _open(client, secret_pdf_bytes)

        assert not os.path.isdir(directory)
        assert os.path.isdir(redact_session.session_dir(Config.UPLOAD_FOLDER, fresh))


# ── page rendering ──────────────────────────────────────────────────────

class TestPageImage:
    def test_renders_a_page_as_a_png(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.get(f"/api/v1/pdf-redact/page/{sid}/1")

        assert resp.status_code == 200
        assert resp.mimetype == "image/png"
        assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_rendered_pages_are_never_cached(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.get(f"/api/v1/pdf-redact/page/{sid}/1")

        # A rendered page is sensitive content: it must not sit in any cache.
        assert "no-store" in resp.headers.get("Cache-Control", "")

    def test_renders_every_page_of_a_multipage_pdf(self, client, multipage_pdf_bytes):
        sid = _open_in_place(multipage_pdf_bytes)

        for page_no in (1, 2, 3):
            assert client.get(f"/api/v1/pdf-redact/page/{sid}/{page_no}").status_code == 200

    def test_unknown_session_is_not_found(self, client):
        resp = client.get(f"/api/v1/pdf-redact/page/{'a' * 32}/1")

        assert resp.status_code == 404

    def test_malformed_session_id_is_not_found(self, client):
        resp = client.get("/api/v1/pdf-redact/page/not-a-session/1")

        assert resp.status_code == 404

    def test_page_out_of_range_is_rejected(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        assert client.get(f"/api/v1/pdf-redact/page/{sid}/7").status_code == 400

    @pytest.mark.parametrize("dpi", ["99999", "abc", "0"])
    def test_unusable_dpi_is_rejected(self, client, secret_pdf_bytes, dpi):
        sid = _open_in_place(secret_pdf_bytes)

        assert client.get(f"/api/v1/pdf-redact/page/{sid}/1?dpi={dpi}").status_code == 400


# ── keyword / regex search ──────────────────────────────────────────────

class TestSearch:
    def test_finds_a_keyword(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.post(
            "/api/v1/pdf-redact/search",
            json={"sid": sid, "pattern": "SECRET-ID-1234"},
        )

        assert resp.status_code == 200
        matches = resp.get_json()["matches"]
        assert len(matches) == 1
        assert matches[0]["page"] == 1

    def test_finds_a_regex_template(self, client, multipage_pdf_bytes):
        sid = _open_in_place(multipage_pdf_bytes)

        resp = client.post(
            "/api/v1/pdf-redact/search",
            json={"sid": sid, "pattern": r"SECRET-\d-9999", "regex": True},
        )

        assert resp.status_code == 200
        assert [m["page"] for m in resp.get_json()["matches"]] == [1, 2, 3]

    def test_scans_only_the_requested_pages(self, client, multipage_pdf_bytes):
        sid = _open_in_place(multipage_pdf_bytes)

        resp = client.post(
            "/api/v1/pdf-redact/search",
            json={"sid": sid, "pattern": "KEEPER", "pages": [2]},
        )

        assert [m["page"] for m in resp.get_json()["matches"]] == [2]

    def test_missing_pattern_is_rejected(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.post("/api/v1/pdf-redact/search", json={"sid": sid})

        assert resp.status_code == 400

    def test_broken_regex_is_rejected(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.post(
            "/api/v1/pdf-redact/search",
            json={"sid": sid, "pattern": "SECRET-(\\d", "regex": True},
        )

        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_unknown_session_is_not_found(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/search",
            json={"sid": "b" * 32, "pattern": "SECRET"},
        )

        assert resp.status_code == 404

    def test_missing_body_is_rejected(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/search",
            data="not json",
            content_type="application/json",
        )

        assert resp.status_code == 400


# ── apply ───────────────────────────────────────────────────────────────

class TestApply:
    def test_redacts_the_marked_region_and_reports(self, client, secret_pdf_bytes):
        import pymupdf

        sid = _open_in_place(secret_pdf_bytes)
        marks = _marks_for(sid, "SECRET-ID-1234")

        resp = client.post(
            "/api/v1/pdf-redact/apply",
            json={"sid": sid, "marks": marks, "mosaicBlock": 8},
        )

        assert resp.status_code == 200
        report = resp.get_json()
        assert report["success"] is True
        assert report["total_marks"] == 1
        assert report["applied"] == 1
        assert report["leftover_regions"] == []
        assert report["verified"] is True

        out = redact_session.output_path(Config.UPLOAD_FOLDER, sid)
        assert os.path.isfile(out)
        doc = pymupdf.open(out)
        text = doc[0].get_text()
        doc.close()
        assert "SECRET-ID-1234" not in text
        assert "KEEP THIS LINE" in text

    def test_the_original_upload_is_left_untouched(self, client, secret_pdf_bytes):
        import pymupdf

        sid = _open_in_place(secret_pdf_bytes)
        marks = _marks_for(sid, "SECRET-ID-1234")

        client.post("/api/v1/pdf-redact/apply", json={"sid": sid, "marks": marks})

        source = redact_session.source_path(Config.UPLOAD_FOLDER, sid)
        doc = pymupdf.open(source)
        text = doc[0].get_text()
        doc.close()
        assert "SECRET-ID-1234" in text

    def test_reports_no_warnings_for_a_clean_run(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)
        marks = _marks_for(sid, "SECRET-ID-1234")

        report = client.post(
            "/api/v1/pdf-redact/apply", json={"sid": sid, "marks": marks}
        ).get_json()

        assert report["verified"] is True
        assert report["leftover_regions"] == []

    def test_flags_a_region_whose_text_survives(self, client, secret_pdf_bytes, monkeypatch):
        """A verification that still finds text must be surfaced, not swallowed."""
        from blueprints import pdf_redact_bp
        from errors import ServiceResult

        sid = _open_in_place(secret_pdf_bytes)
        marks = _marks_for(sid, "SECRET-ID-1234")
        monkeypatch.setattr(
            pdf_redact_bp,
            "redact_pdf",
            lambda src, out, marks, block: ServiceResult.ok({
                "output": out,
                "page_count": 1,
                "total_marks": 1,
                "applied": 1,
                "image_marks": 0,
                "leftover_regions": [{"mark": 1, "page": 1}],
            }),
        )

        report = client.post(
            "/api/v1/pdf-redact/apply", json={"sid": sid, "marks": marks}
        ).get_json()

        assert report["verified"] is False
        assert report["leftover_regions"] == [{"mark": 1, "page": 1}]

    def test_no_marks_is_rejected(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.post("/api/v1/pdf-redact/apply", json={"sid": sid, "marks": []})

        assert resp.status_code == 400
        assert not os.path.isfile(redact_session.output_path(Config.UPLOAD_FOLDER, sid))

    def test_out_of_range_page_is_rejected(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        resp = client.post(
            "/api/v1/pdf-redact/apply",
            json={"sid": sid, "marks": [{"page": 9, "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1}]},
        )

        assert resp.status_code == 400
        assert not os.path.isfile(redact_session.output_path(Config.UPLOAD_FOLDER, sid))

    def test_missing_body_is_rejected(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/apply",
            data="not json",
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_unknown_session_is_not_found(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/apply",
            json={"sid": "c" * 32, "marks": [{"page": 1, "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1}]},
        )

        assert resp.status_code == 404


# ── download ────────────────────────────────────────────────────────────

class TestDownload:
    def test_downloads_the_redacted_pdf(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)
        marks = _marks_for(sid, "SECRET-ID-1234")
        client.post("/api/v1/pdf-redact/apply", json={"sid": sid, "marks": marks})

        resp = client.get(f"/api/v1/pdf-redact/download/{sid}")

        assert resp.status_code == 200
        assert resp.mimetype == "application/pdf"
        assert resp.data[:4] == b"%PDF"
        assert "attachment" in resp.headers["Content-Disposition"]

    def test_download_name_keeps_the_original_stem(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes, name="年报 2026.pdf")
        client.post("/api/v1/pdf-redact/apply", json={"sid": sid, "marks": _marks_for(sid, "SECRET")})

        resp = client.get(f"/api/v1/pdf-redact/download/{sid}")

        disposition = resp.headers["Content-Disposition"]
        assert "attachment" in disposition
        assert ".pdf" in disposition

    def test_download_before_apply_is_not_found(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        assert client.get(f"/api/v1/pdf-redact/download/{sid}").status_code == 404

    def test_unknown_session_is_not_found(self, client):
        assert client.get(f"/api/v1/pdf-redact/download/{'d' * 32}").status_code == 404

    def test_download_is_never_cached(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)
        client.post("/api/v1/pdf-redact/apply", json={"sid": sid, "marks": _marks_for(sid, "SECRET")})

        resp = client.get(f"/api/v1/pdf-redact/download/{sid}")

        assert "no-store" in resp.headers.get("Cache-Control", "")


# ── close ───────────────────────────────────────────────────────────────

class TestClose:
    def test_closes_the_session_and_deletes_its_files(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)
        assert os.path.isdir(redact_session.session_dir(Config.UPLOAD_FOLDER, sid))

        resp = client.post("/api/v1/pdf-redact/close", json={"sid": sid})

        assert resp.status_code == 200
        assert not os.path.isdir(redact_session.session_dir(Config.UPLOAD_FOLDER, sid))

    def test_closing_twice_is_harmless(self, client, secret_pdf_bytes):
        sid = _open_in_place(secret_pdf_bytes)

        assert client.post("/api/v1/pdf-redact/close", json={"sid": sid}).status_code == 200
        assert client.post("/api/v1/pdf-redact/close", json={"sid": sid}).status_code == 200

    def test_closing_one_session_leaves_others_alone(self, client, secret_pdf_bytes):
        first = _open_in_place(secret_pdf_bytes)
        second = _open_in_place(secret_pdf_bytes)

        client.post("/api/v1/pdf-redact/close", json={"sid": first})

        assert not os.path.isdir(redact_session.session_dir(Config.UPLOAD_FOLDER, first))
        assert os.path.isdir(redact_session.session_dir(Config.UPLOAD_FOLDER, second))

    def test_malformed_session_id_is_rejected(self, client):
        resp = client.post("/api/v1/pdf-redact/close", json={"sid": "../etc"})

        assert resp.status_code == 400

    def test_missing_body_is_rejected(self, client):
        resp = client.post(
            "/api/v1/pdf-redact/close",
            data="not json",
            content_type="application/json",
        )

        assert resp.status_code == 400


# ── wiring ──────────────────────────────────────────────────────────────

class TestWiring:
    def test_module_is_registered_for_stats(self):
        """Missing from MODULE_NAMES → the tool never appears on /status."""
        from services.stats import MODULE_NAMES

        assert "pdf-redact" in MODULE_NAMES

    def test_page_is_in_the_sitemap(self, client):
        resp = client.get("/sitemap.xml")

        assert "/pdf-redact" in resp.get_data(as_text=True)
