"""File upload route tests: pdf-merge."""

import io
from unittest.mock import patch

from errors import ServiceResult, ErrorCode


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
