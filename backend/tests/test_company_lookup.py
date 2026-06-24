"""Tests for company lookup module — models, service, and API routes."""

import json
import os
import tempfile

import pytest

from errors import ErrorCode, ServiceResult
from models import CompanyRecord, init_db, _normalize_company_name


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """In-memory CompanyRecord backed by a temp SQLite file."""
    _, db_path = tempfile.mkstemp(suffix=".db")
    init_db(db_path)
    cr = CompanyRecord(db_path)
    yield cr
    os.unlink(db_path)


@pytest.fixture
def seeded_db(db):
    """DB pre-populated with a few companies."""
    db.upsert("tencent", "https://www.tencent.com")
    db.upsert("alibaba", "https://www.alibaba.com")
    db.upsert("huawei", "https://www.huawei.com")
    return db


# ── Model: _normalize_company_name ───────────────────────────────────────

class TestNormalizeCompanyName:
    def test_strips_chinese_suffixes(self):
        assert _normalize_company_name("腾讯科技有限公司") == "腾讯科技"
        assert _normalize_company_name("阿里巴巴集团控股有限公司") == "阿里巴巴集团控股"

    def test_strips_english_suffixes(self):
        assert _normalize_company_name("Apple Inc.") == "apple"
        assert _normalize_company_name("Microsoft Corporation") == "microsoft"

    def test_lowercases(self):
        assert _normalize_company_name("GOOGLE") == "google"

    def test_strips_whitespace(self):
        assert _normalize_company_name("  华为  ") == "华为"

    def test_empty_string(self):
        assert _normalize_company_name("") == ""


# ── Model: CompanyRecord CRUD ────────────────────────────────────────────

class TestCompanyRecordCRUD:
    def test_upsert_creates_new(self, db):
        db.upsert("testcorp", "https://testcorp.com")
        assert db.count() == 1

    def test_upsert_updates_existing(self, db):
        db.upsert("testcorp", "https://old.com")
        db.upsert("testcorp", "https://new.com")
        found = db.find_by_name("testcorp")
        assert found["website"] == "https://new.com"
        assert db.count() == 1

    def test_find_by_name_uses_normalization(self, db):
        # Store with full Chinese name, find with normalized variant
        db.upsert("腾讯科技", "https://www.tencent.com")
        # Lookup with the same name but different suffix should still match
        found = db.find_by_name("腾讯科技有限公司")
        assert found is not None
        assert found["website"] == "https://www.tencent.com"

    def test_find_by_name_miss(self, db):
        assert db.find_by_name("nonexistent") is None

    def test_confirm_updates_timestamp(self, db):
        db.confirm("newco", "https://newco.com")
        found = db.find_by_name("newco")
        assert found is not None
        assert found["confirmed_at"] is not None

    def test_search_by_name_fuzzy(self, seeded_db):
        results = seeded_db.search_by_name("ten")
        assert len(results) >= 1

    def test_search_by_name_no_match(self, db):
        assert db.search_by_name("zzznotexist") == []

    def test_list_all_pagination(self, seeded_db):
        page1 = seeded_db.list_all(page=1, size=2)
        assert len(page1) <= 2
        page2 = seeded_db.list_all(page=2, size=2)
        assert len(page2) <= 2

    def test_count(self, seeded_db):
        assert seeded_db.count() == 3


# ── Model: export_all / import_batch ─────────────────────────────────────

class TestExportImport:
    def test_export_all_returns_all_records(self, seeded_db):
        records = seeded_db.export_all()
        assert len(records) == 3
        names = {r["name"] for r in records}
        assert "tencent" in names
        assert "alibaba" in names
        assert "huawei" in names

    def test_export_all_empty_db(self, db):
        assert db.export_all() == []

    def test_import_batch_success(self, db):
        records = [
            {"name": "baidu", "website": "https://www.baidu.com"},
            {"name": "jd", "website": "https://www.jd.com"},
        ]
        result = db.import_batch(records)
        assert result["imported"] == 2
        assert result["skipped"] == 0
        assert db.count() == 2

    def test_import_batch_skips_invalid(self, db):
        records = [
            {"name": "", "website": "https://x.com"},          # empty name
            {"name": "valid", "website": ""},                   # empty website
            {"name": "badurl", "website": "not-a-url"},         # no scheme
            {"name": "good", "website": "https://good.com"},    # valid
        ]
        result = db.import_batch(records)
        assert result["imported"] == 1
        assert result["skipped"] == 3
        assert len(result["errors"]) == 3

    def test_import_batch_upserts(self, db):
        db.upsert("existing", "https://old.com")
        records = [{"name": "existing", "website": "https://new.com"}]
        result = db.import_batch(records)
        assert result["imported"] == 1
        assert db.find_by_name("existing")["website"] == "https://new.com"

    def test_export_import_roundtrip(self, db):
        db.upsert("c1", "https://c1.com")
        db.upsert("c2", "https://c2.com")
        exported = db.export_all()
        db2 = CompanyRecord(db.db_path)
        db2.import_batch(exported)
        assert db2.count() == 2


# ── Service: lookup_company ──────────────────────────────────────────────

class TestLookupCompany:
    def test_empty_name_fails(self, db):
        from services.company_lookup import lookup_company
        result = lookup_company("", db)
        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_local_hit_returns_immediately(self, seeded_db):
        from services.company_lookup import lookup_company
        # "tencent" is in local DB — should hit without API call
        result = lookup_company("tencent", seeded_db)
        assert result.success
        assert result.data["source"] == "local"
        assert result.data["website"] == "https://www.tencent.com"
        assert result.data["confirmed"] is True

    def test_returns_service_result(self, db):
        from services.company_lookup import lookup_company
        result = lookup_company("some company", db)
        assert isinstance(result, ServiceResult)


# ── Service: confirm_company ─────────────────────────────────────────────

class TestConfirmCompany:
    def test_saves_and_returns(self, db):
        from services.company_lookup import confirm_company
        result = confirm_company("newco", "https://newco.com", db)
        assert result.success
        assert result.data["saved"] is True
        assert result.data["confirmed"] is True

    def test_empty_name_fails(self, db):
        from services.company_lookup import confirm_company
        result = confirm_company("", "https://x.com", db)
        assert not result.success
        assert result.error == ErrorCode.VALIDATION_ERROR

    def test_invalid_url_fails(self, db):
        from services.company_lookup import confirm_company
        result = confirm_company("name", "not-a-url", db)
        assert not result.success

    def test_corrected_values_used(self, db):
        from services.company_lookup import confirm_company
        result = confirm_company(
            "oldname", "https://old.com", db,
            corrected_name="newname", corrected_website="https://new.com",
        )
        assert result.success
        found = db.find_by_name("newname")
        assert found is not None
        assert found["website"] == "https://new.com"


# ── Service: batch_lookup ────────────────────────────────────────────────

class TestBatchLookup:
    def test_local_hits_returned(self, seeded_db):
        from services.company_lookup import batch_lookup
        results = batch_lookup(["tencent", "alibaba"], seeded_db.db_path)
        assert len(results) == 2
        assert all(r["source"] == "local" for r in results)

    def test_empty_name_handled(self, db):
        from services.company_lookup import batch_lookup
        results = batch_lookup(["", "   "], db.db_path)
        assert len(results) == 2
        assert all(r["source"] == "error" for r in results)


# ── Blueprint: API routes ────────────────────────────────────────────────

class TestCompanyLookupAPI:
    def test_single_lookup_empty_name(self, client):
        resp = client.post("/api/v1/company-lookup",
                           data=json.dumps({"name": ""}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_single_lookup_missing_body(self, client):
        resp = client.post("/api/v1/company-lookup",
                           data=json.dumps({}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_batch_lookup_empty_list(self, client):
        resp = client.post("/api/v1/company-lookup/batch",
                           data=json.dumps({"names": []}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_batch_lookup_not_a_list(self, client):
        resp = client.post("/api/v1/company-lookup/batch",
                           data=json.dumps({"names": "not a list"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_confirm_empty_name(self, client):
        resp = client.post("/api/v1/company-lookup/confirm",
                           data=json.dumps({"name": "", "website": "https://x.com"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_confirm_invalid_url(self, client):
        resp = client.post("/api/v1/company-lookup/confirm",
                           data=json.dumps({"name": "test", "website": "bad"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_export_csv(self, client):
        resp = client.get("/api/v1/company-lookup/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type

    def test_export_json(self, client):
        resp = client.get("/api/v1/company-lookup/export?format=json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_import_no_file(self, client):
        resp = client.post("/api/v1/company-lookup/import")
        assert resp.status_code == 400

    def test_import_empty_csv(self, client, tmp_dir):
        csv_path = os.path.join(tmp_dir, "empty.csv")
        with open(csv_path, "w") as f:
            f.write("name,website\n")
        with open(csv_path, "rb") as f:
            resp = client.post("/api/v1/company-lookup/import",
                               data={"file": (f, "empty.csv")},
                               content_type="multipart/form-data")
        assert resp.status_code == 400  # no valid records

    def test_import_valid_csv(self, client, tmp_dir):
        csv_path = os.path.join(tmp_dir, "test.csv")
        with open(csv_path, "w") as f:
            f.write("name,website\n")
            f.write("TestCorp,https://testcorp.com\n")
            f.write("AnotherCo,https://another.com\n")
        with open(csv_path, "rb") as f:
            resp = client.post("/api/v1/company-lookup/import",
                               data={"file": (f, "test.csv")},
                               content_type="multipart/form-data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["data"]["imported"] == 2

    def test_confirm_success(self, client):
        resp = client.post("/api/v1/company-lookup/confirm",
                           data=json.dumps({"name": "TestCo", "website": "https://testco.com"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["data"]["saved"] is True

    def test_full_roundtrip(self, client, tmp_dir):
        """Confirm → export CSV → import back."""
        # Confirm a company with a simple name that won't be suffix-stripped
        client.post("/api/v1/company-lookup/confirm",
                    data=json.dumps({"name": "RoundtripTest", "website": "https://rt.com"}),
                    content_type="application/json")
        # Export
        resp = client.get("/api/v1/company-lookup/export")
        assert resp.status_code == 200
        csv_data = resp.data.decode("utf-8-sig")
        assert "https://rt.com" in csv_data

        # Write export to temp file and re-import
        csv_path = os.path.join(tmp_dir, "reimport.csv")
        with open(csv_path, "w") as f:
            f.write(csv_data)
        with open(csv_path, "rb") as f:
            resp = client.post("/api/v1/company-lookup/import",
                               data={"file": (f, "reimport.csv")},
                               content_type="multipart/form-data")
        assert resp.status_code == 200
