"""Critical path route tests: health, preview, convert, download, tasks."""

import io
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from errors import ServiceResult, ErrorCode


class TestHealthEndpoint:
    """GET /api/v1/health — basic liveness check."""

    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "deps" in data
        assert "ffmpeg" in data["deps"]
        assert "pandoc" in data["deps"]


class TestPreviewEndpoint:
    """POST /api/v1/preview — Markdown to HTML rendering."""

    def test_preview_renders_markdown(self, client):
        resp = client.post(
            "/api/v1/preview",
            json={"content": "# Hello\n\nThis is **bold**."},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "html" in data
        assert "<h1>" in data["html"] or "<h1" in data["html"]
        assert "<strong>bold</strong>" in data["html"]

    def test_preview_strips_dangerous_tags(self, client):
        resp = client.post(
            "/api/v1/preview",
            json={"content": "Safe <script>alert('xss')</script> text"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "<script>" not in data["html"]

    def test_preview_empty_content_returns_422(self, client):
        resp = client.post(
            "/api/v1/preview",
            json={"content": ""},
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_preview_missing_content_returns_422(self, client):
        resp = client.post(
            "/api/v1/preview",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_preview_no_json_returns_422(self, client):
        resp = client.post("/api/v1/preview", content_type="application/json")
        assert resp.status_code == 422


class TestConvertEndpoint:
    """POST /api/v1/convert — Markdown to DOCX conversion."""

    @patch("blueprints.convert.md_to_docx")
    @patch("blueprints.convert.format_docx")
    def test_convert_with_json_content(self, mock_format, mock_convert, client, app):
        mock_convert.return_value = ServiceResult.ok("测试文档")
        mock_format.return_value = ServiceResult.ok(None)

        resp = client.post(
            "/api/v1/convert",
            json={"content": "# Test\n\nContent here."},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "download_id" in data
        assert data["filename"].endswith(".docx")
        mock_convert.assert_called_once()

    @patch("blueprints.convert.md_to_docx")
    @patch("blueprints.convert.format_docx")
    def test_convert_with_file_upload(self, mock_format, mock_convert, client, app):
        mock_convert.return_value = ServiceResult.ok("文档标题")
        mock_format.return_value = ServiceResult.ok(None)

        md_content = b"# Uploaded File\n\nMarkdown content."
        data = {"file": (io.BytesIO(md_content), "test.md")}
        resp = client.post(
            "/api/v1/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert result["title"] == "文档标题"

    def test_convert_no_content_returns_400(self, client):
        resp = client.post(
            "/api/v1/convert",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_convert_empty_content_returns_400(self, client):
        resp = client.post(
            "/api/v1/convert",
            json={"content": "   "},
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("blueprints.convert.md_to_docx")
    def test_convert_service_failure_returns_400(self, mock_convert, client, app):
        mock_convert.return_value = ServiceResult.fail(
            ErrorCode.CONVERSION_FAILED, "Pandoc not available"
        )

        resp = client.post(
            "/api/v1/convert",
            json={"content": "# Test"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data


class TestDownloadEndpoint:
    """GET /api/v1/download/<filename> — file serving with Range support."""

    def test_download_missing_file_returns_404(self, client):
        resp = client.get("/api/v1/download/nonexistent.docx")
        assert resp.status_code == 404

    def test_download_invalid_extension_returns_400(self, client, app):
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, "test.exe")
        with open(test_file, "wb") as f:
            f.write(b"fake executable")

        resp = client.get("/api/v1/download/test.exe")
        assert resp.status_code == 400

    def test_download_path_traversal_blocked(self, client, app):
        """Traversal must never expose a file outside UPLOAD_FOLDER.

        Asserts on the absence of the file's contents rather than on a status
        code: unmatched paths fall through to the SPA fallback and legitimately
        answer 200 with index.html when the frontend has been built.
        """
        upload_dir = app.config["UPLOAD_FOLDER"]
        sentinel = os.path.join(os.path.dirname(upload_dir), "traversal-sentinel.txt")
        with open(sentinel, "w") as f:
            f.write("SECRET-SENTINEL")
        name = os.path.basename(sentinel)

        for path in (
            f"/api/v1/download/../{name}",
            f"/api/v1/download/..%2f{name}",
            f"/api/v1/download/..\\{name}",
        ):
            resp = client.get(path)
            assert b"SECRET-SENTINEL" not in resp.data

    def test_download_valid_file(self, client, app):
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, "test.docx")
        content = b"fake docx content for testing"
        with open(test_file, "wb") as f:
            f.write(content)

        resp = client.get("/api/v1/download/test.docx")
        assert resp.status_code == 200
        assert resp.data == content
        assert resp.headers.get("Accept-Ranges") == "bytes"

    def test_download_with_range_request(self, client, app):
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, "range_test.docx")
        content = b"0123456789ABCDEF"
        with open(test_file, "wb") as f:
            f.write(content)

        resp = client.get(
            "/api/v1/download/range_test.docx",
            headers={"Range": "bytes=0-4"},
        )
        assert resp.status_code == 206
        assert resp.data == b"01234"
        assert "Content-Range" in resp.headers
        assert resp.headers["Content-Range"] == "bytes 0-4/16"

    def test_download_range_full_file(self, client, app):
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, "full_range.md")
        content = b"Full file content"
        with open(test_file, "wb") as f:
            f.write(content)

        resp = client.get(
            "/api/v1/download/full_range.md",
            headers={"Range": "bytes=0-"},
        )
        assert resp.status_code == 206
        assert resp.data == content

    @pytest.mark.parametrize(
        "ext", ["pdf", "doc", "docx", "ppt", "pptx", "png", "jpg", "jpeg"]
    )
    def test_download_allows_mineru_source_formats(self, client, app, ext):
        """MinerU fetches our own uploaded files back over this endpoint."""
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, f"source.{ext}")
        content = b"source bytes"
        with open(test_file, "wb") as f:
            f.write(content)

        resp = client.get(f"/api/v1/download/source.{ext}")

        assert resp.status_code == 200, resp.get_data(as_text=True)

    def test_download_reports_binary_mimetype(self, client, app):
        upload_dir = app.config["UPLOAD_FOLDER"]
        test_file = os.path.join(upload_dir, "source.pdf")
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4\n")

        resp = client.get("/api/v1/download/source.pdf")

        assert resp.mimetype == "application/pdf"


class TestTaskStatusEndpoint:
    """GET /api/v1/tasks/<task_id> — task status lookup."""

    @patch("blueprints.download._get_models")
    def test_task_not_found_returns_404(self, mock_get_models, client):
        mock_record = MagicMock()
        mock_record.get_by_id.return_value = None
        mock_get_models.return_value = (mock_record, MagicMock())

        resp = client.get("/api/v1/tasks/nonexistent-task-id")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["code"] == 404
        assert "未找到" in data["msg"]

    @patch("blueprints.download._get_models")
    def test_task_found_returns_200(self, mock_get_models, client):
        mock_record = MagicMock()
        mock_record.get_by_id.return_value = {
            "id": "test-task-123",
            "status": "success",
            "progress": 100,
            "updated_at": "2026-09-21T10:00:00",
        }
        mock_get_models.return_value = (mock_record, MagicMock())

        resp = client.get("/api/v1/tasks/test-task-123")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 200
        assert data["data"]["id"] == "test-task-123"
        assert data["data"]["status"] == "success"


class TestStatsEndpoint:
    """GET /api/v1/stats — conversion counter."""

    def test_stats_returns_count(self, client):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_conversions" in data
        assert isinstance(data["total_conversions"], int)
