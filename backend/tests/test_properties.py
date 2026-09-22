"""Tests for properties service."""

import io
import os
import zipfile

from services.properties import batch_modify_properties, read_properties, modify_properties
from errors import ServiceResult

CORE_XML = "docProps/core.xml"
EMPTY_PROPS = {
    "created": "",
    "modified": "",
    "creator": "",
    "last_modified_by": "",
}


def _make_docx(path, strip_core_xml: bool = False) -> str:
    """Build a DOCX, optionally dropping its docProps/core.xml part."""
    from docx import Document

    doc = Document()
    doc.add_paragraph("hello")
    path = str(path)
    if not strip_core_xml:
        doc.save(path)
        return path

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    with zipfile.ZipFile(buf) as src, zipfile.ZipFile(path, "w") as dst:
        for name in src.namelist():
            if name != CORE_XML:
                dst.writestr(name, src.read(name))
    return path


def _make_plain_zip(path) -> str:
    """A valid ZIP with the right magic bytes that is not an Office document."""
    path = str(path)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("readme.txt", "not an office document")
    return path


class TestReadProperties:
    def test_missing_file_returns_failure(self, tmp_dir):
        """Non-existent file → ServiceResult.fail."""
        result = read_properties(os.path.join(tmp_dir, "missing.docx"))
        assert not result.success

    def test_txt_file_returns_failure(self, sample_txt):
        """Non-Office file → failure."""
        result = read_properties(sample_txt)
        assert not result.success

    def test_docx_without_core_xml_still_returns_service_result(self, tmp_path):
        """A document with no docProps/core.xml yields empty properties, not a raw dict."""
        path = _make_docx(tmp_path / "nocore.docx", strip_core_xml=True)

        result = read_properties(path)

        assert isinstance(result, ServiceResult)
        assert result.success
        assert result.data == EMPTY_PROPS

    def test_docx_without_core_xml_endpoint_returns_200(self, client, tmp_path):
        path = _make_docx(tmp_path / "nocore.docx", strip_core_xml=True)
        with open(path, "rb") as f:
            payload = f.read()

        resp = client.post(
            "/api/v1/properties/info",
            data={"file": (io.BytesIO(payload), "nocore.docx")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200, resp.get_data(as_text=True)
        assert resp.get_json()["properties"] == EMPTY_PROPS


class TestModifyProperties:
    def test_missing_file_returns_failure(self, tmp_dir):
        """Non-existent file → failure."""
        result = modify_properties(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
            {"creator": "test"},
        )
        assert not result.success

    def test_returns_service_result(self, tmp_dir):
        """Always returns ServiceResult."""
        result = modify_properties(
            os.path.join(tmp_dir, "missing.docx"),
            os.path.join(tmp_dir, "out.docx"),
            {},
        )
        assert isinstance(result, ServiceResult)
        assert hasattr(result, "success")


class TestBatchModifyProperties:
    def test_unmodifiable_file_is_reported_as_failure(self, tmp_path):
        """A member that cannot be processed must not be reported as a success."""
        good = _make_docx(tmp_path / "good.docx")
        bad = _make_plain_zip(tmp_path / "bad.docx")
        out = tmp_path / "out"
        out.mkdir()

        result = batch_modify_properties([good, bad], str(out), {"creator": "x"})

        assert result.success
        by_name = {r["filename"]: r for r in result.data}
        assert by_name["good.docx"]["success"] is True
        assert by_name["bad.docx"]["success"] is False
        assert by_name["bad.docx"]["error"]
        assert (out / "good.docx").is_file()
        assert not (out / "bad.docx").exists()

    def test_empty_list_returns_failure(self, tmp_path):
        result = batch_modify_properties([], str(tmp_path), {"creator": "x"})
        assert not result.success


class TestBatchEndpoint:
    def test_partial_failure_returns_zip_of_successes(self, client, tmp_path):
        good = _make_docx(tmp_path / "good.docx")
        bad = _make_plain_zip(tmp_path / "bad.docx")
        with open(good, "rb") as f:
            good_bytes = f.read()
        with open(bad, "rb") as f:
            bad_bytes = f.read()

        resp = client.post(
            "/api/v1/properties/batch",
            data={
                "files": [
                    (io.BytesIO(good_bytes), "good.docx"),
                    (io.BytesIO(bad_bytes), "bad.docx"),
                ],
                "creator": "batch-author",
            },
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200, resp.get_data(as_text=True)
        with zipfile.ZipFile(io.BytesIO(resp.data)) as zf:
            names = zf.namelist()
        # Uploads are stored with a uuid prefix, so the archive member carries it.
        assert len(names) == 1
        assert names[0].endswith("good.docx")

    def test_all_failures_return_400_not_an_empty_zip(self, client, tmp_path):
        bad = _make_plain_zip(tmp_path / "bad.docx")
        with open(bad, "rb") as f:
            bad_bytes = f.read()

        resp = client.post(
            "/api/v1/properties/batch",
            data={
                "files": [(io.BytesIO(bad_bytes), "bad.docx")],
                "creator": "batch-author",
            },
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400, resp.data[:200]
