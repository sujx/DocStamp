"""File upload route tests: watermark, pdf-merge."""

import io
import json
import os
from unittest.mock import patch, MagicMock

import pytest

from errors import ServiceResult, ErrorCode


class TestWatermarkAddEndpoint:
    """POST /api/v1/watermark — add watermark to PDF/DOCX."""

    def test_watermark_no_file_returns_400(self, client):
        resp = client.post("/api/v1/watermark")
        assert resp.status_code == 400

    def test_watermark_empty_filename_returns_400(self, client):
        data = {"file": (io.BytesIO(b"content"), "")}
        resp = client.post(
            "/api/v1/watermark",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_watermark_text_type_without_text_returns_400(self, client, sample_pdf_file):
        data = {
            "file": (sample_pdf_file, "test.pdf"),
            "params": json.dumps({"watermark_type": "text"}),
        }
        resp = client.post(
            "/api/v1/watermark",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    @patch("blueprints.watermark_bp.add_watermark")
    def test_watermark_text_success(self, mock_add, client, app, sample_pdf_file):
        output_content = b"watermarked pdf content"
        mock_add.return_value = ServiceResult.ok(None)

        def fake_add(filepath, output_path, params, image_path=None):
            with open(output_path, "wb") as f:
                f.write(output_content)
            return ServiceResult.ok(None)

        mock_add.side_effect = fake_add

        data = {
            "file": (sample_pdf_file, "test.pdf"),
            "params": json.dumps({
                "watermark_type": "text",
                "text": "CONFIDENTIAL",
                "font_size": 24,
            }),
        }
        resp = client.post(
            "/api/v1/watermark",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/octet-stream" or "pdf" in resp.content_type

    @patch("blueprints.watermark_bp.add_watermark")
    def test_watermark_service_failure_returns_400(self, mock_add, client, sample_pdf_file):
        mock_add.return_value = ServiceResult.fail(
            ErrorCode.PDF_READ_ERROR, "Invalid PDF"
        )

        data = {
            "file": (sample_pdf_file, "test.pdf"),
            "params": json.dumps({
                "watermark_type": "text",
                "text": "TEST",
            }),
        }
        resp = client.post(
            "/api/v1/watermark",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data


class TestWatermarkRemoveEndpoint:
    """POST /api/v1/watermark/remove — remove watermark from PDF/DOCX."""

    def test_remove_no_file_returns_400(self, client):
        resp = client.post("/api/v1/watermark/remove")
        assert resp.status_code == 400

    @patch("blueprints.watermark_bp.remove_watermark")
    def test_remove_success(self, mock_remove, client, app, sample_pdf_file):
        output_content = b"cleaned pdf content"
        mock_remove.return_value = ServiceResult.ok(None)

        def fake_remove(filepath, output_path):
            with open(output_path, "wb") as f:
                f.write(output_content)
            return ServiceResult.ok(None)

        mock_remove.side_effect = fake_remove

        data = {"file": (sample_pdf_file, "test.pdf")}
        resp = client.post(
            "/api/v1/watermark/remove",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200


class TestPdfMergeEndpoint:
    """POST /api/v1/pdf-merge — merge multiple PDFs."""

    def test_merge_no_files_returns_400(self, client):
        resp = client.post("/api/v1/pdf-merge")
        assert resp.status_code == 400

    def test_merge_single_file_returns_400(self, client, sample_pdf_file):
        data = {"files": [(sample_pdf_file, "single.pdf")]}
        resp = client.post(
            "/api/v1/pdf-merge",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "2" in data["error"] or "两" in data["error"]

    @patch("blueprints.pdf_merge_bp.merge_pdfs")
    def test_merge_two_files_success(self, mock_merge, client, app, sample_pdf_bytes):
        output_content = b"merged pdf content"
        mock_merge.return_value = ServiceResult.ok(None)

        def fake_merge(filepaths, output_path):
            with open(output_path, "wb") as f:
                f.write(output_content)
            return ServiceResult.ok(None)

        mock_merge.side_effect = fake_merge

        pdf1 = io.BytesIO(sample_pdf_bytes)
        pdf2 = io.BytesIO(sample_pdf_bytes)
        data = {
            "files": [
                (pdf1, "file1.pdf"),
                (pdf2, "file2.pdf"),
            ],
        }
        resp = client.post(
            "/api/v1/pdf-merge",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

    @patch("blueprints.pdf_merge_bp.merge_pdfs")
    def test_merge_with_custom_filename(self, mock_merge, client, app, sample_pdf_bytes):
        mock_merge.return_value = ServiceResult.ok(None)

        def fake_merge(filepaths, output_path):
            with open(output_path, "wb") as f:
                f.write(b"merged")
            return ServiceResult.ok(None)

        mock_merge.side_effect = fake_merge

        pdf1 = io.BytesIO(sample_pdf_bytes)
        pdf2 = io.BytesIO(sample_pdf_bytes)
        data = {
            "files": [
                (pdf1, "file1.pdf"),
                (pdf2, "file2.pdf"),
            ],
            "filename": "custom_name.pdf",
        }
        resp = client.post(
            "/api/v1/pdf-merge",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert "custom_name.pdf" in resp.headers.get("Content-Disposition", "")

    @patch("blueprints.pdf_merge_bp.merge_pdfs")
    def test_merge_service_failure_returns_400(self, mock_merge, client, app, sample_pdf_bytes):
        mock_merge.return_value = ServiceResult.fail(
            ErrorCode.PDF_READ_ERROR, "Failed to read PDF"
        )

        pdf1 = io.BytesIO(sample_pdf_bytes)
        pdf2 = io.BytesIO(sample_pdf_bytes)
        data = {
            "files": [
                (pdf1, "file1.pdf"),
                (pdf2, "file2.pdf"),
            ],
        }
        resp = client.post(
            "/api/v1/pdf-merge",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
