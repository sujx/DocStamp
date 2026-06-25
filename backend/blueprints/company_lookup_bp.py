"""Company name → website lookup blueprint.

Endpoints:
    POST /api/v1/company-lookup         — single synchronous lookup
    POST /api/v1/company-lookup/batch   — batch async lookup (Celery + SSE)
    POST /api/v1/company-lookup/confirm — confirm and save to local DB
    GET  /api/v1/company-lookup/export  — export DB as CSV/JSON
    POST /api/v1/company-lookup/import  — import CSV/JSON into DB
"""

import csv
import io
import json

from flask import Blueprint, g, jsonify, request, Response

from config import Config
from models import CompanyRecord, init_db
from schemas import CompanyBatchLookupSchema, CompanyConfirmSchema, CompanyLookupSchema
from services.company_lookup import confirm_company, lookup_company
from utils.rate_limit import rate_limit

company_lookup_bp = Blueprint("company-lookup", __name__)


def _get_company_db() -> CompanyRecord:
    """Get or create CompanyRecord instance for the current request."""
    db_path = Config().TASK_DB_PATH
    init_db(db_path)
    return CompanyRecord(db_path)


@company_lookup_bp.route("/api/v1/company-lookup", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def company_lookup():
    """Look up a single company's official website.

    Checks local DB first, falls back to web search.
    Web results are returned unconfirmed.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({
            "code": 400, "msg": "Company name is required",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    db = _get_company_db()
    result = lookup_company(name, db)

    if not result.success:
        return jsonify({
            "code": 400, "msg": result.message,
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    return jsonify({
        "code": 200,
        "data": result.data,
        "requestId": getattr(g, "request_id", "-"),
    })


@company_lookup_bp.route("/api/v1/company-lookup/batch", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def company_lookup_batch():
    """Batch company lookup. ≤10 synchronous, >10 async via Celery."""
    data = request.get_json(silent=True) or {}
    names = data.get("names") or []

    if not names or not isinstance(names, list):
        return jsonify({
            "code": 400, "msg": "names must be a non-empty list",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    if len(names) > 100:
        return jsonify({
            "code": 400, "msg": "Maximum 100 names per batch request",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    names = [n.strip() for n in names if n and n.strip()]
    if not names:
        return jsonify({
            "code": 400, "msg": "No valid company names provided",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    # All batches are synchronous — local DB first, then single LLM call
    from services.company_lookup import batch_lookup
    db_path = Config().TASK_DB_PATH
    init_db(db_path)
    results = batch_lookup(names, db_path, fast=True)
    return jsonify({
        "code": 200,
        "data": {"results": results, "total": len(names)},
        "requestId": getattr(g, "request_id", "-"),
    })


@company_lookup_bp.route("/api/v1/company-lookup/confirm", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
def company_lookup_confirm():
    """Confirm a company lookup result and save to local database.

    Accepts optional corrected_name and corrected_website if the user
    fixed an incorrect web search result.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    website = (data.get("website") or "").strip()
    corrected_name = (data.get("corrected_name") or "").strip() or None
    corrected_website = (data.get("corrected_website") or "").strip() or None

    if not name:
        return jsonify({
            "code": 400, "msg": "Company name is required",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    if not website:
        return jsonify({
            "code": 400, "msg": "Website URL is required",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    db = _get_company_db()
    result = confirm_company(
        name=name,
        website=website,
        db=db,
        corrected_name=corrected_name,
        corrected_website=corrected_website,
    )

    if not result.success:
        return jsonify({
            "code": 400, "msg": result.message,
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    return jsonify({
        "code": 200,
        "data": result.data,
        "requestId": getattr(g, "request_id", "-"),
    })


# ── Export / Import ────────────────────────────────────────────────────────


@company_lookup_bp.route("/api/v1/company-lookup/export", methods=["GET"])
@rate_limit(max_requests=10, window_seconds=60)
def company_lookup_export():
    """Export all company records as CSV or JSON."""
    fmt = (request.args.get("format") or "csv").lower()
    db = _get_company_db()
    records = db.export_all()

    if fmt == "json":
        return jsonify({"code": 200, "data": records,
                        "requestId": getattr(g, "request_id", "-")})

    output = io.StringIO()
    output.write("﻿")
    writer = csv.writer(output)
    writer.writerow(["name", "website", "source", "confirmed_at", "created_at"])
    for r in records:
        writer.writerow([
            r.get("name", ""), r.get("website", ""), r.get("source", ""),
            r.get("confirmed_at", ""), r.get("created_at", ""),
        ])
    csv_data = output.getvalue()
    output.close()
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=company_records.csv"},
    )


@company_lookup_bp.route("/api/v1/company-lookup/import", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def company_lookup_import():
    """Import company records from uploaded CSV or JSON file."""
    file = request.files.get("file")
    if not file:
        return jsonify({
            "code": 400, "msg": "No file provided",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    filename = (file.filename or "").lower()
    try:
        content = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            file.seek(0)
            content = file.read().decode("gbk")
        except Exception:
            return jsonify({
                "code": 400, "msg": "Cannot decode file. Use UTF-8 or GBK encoding.",
                "requestId": getattr(g, "request_id", "-"),
            }), 400

    records = []
    if filename.endswith(".json"):
        try:
            data = json.loads(content)
            records = data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return jsonify({
                "code": 400, "msg": "Invalid JSON file",
                "requestId": getattr(g, "request_id", "-"),
            }), 400
    else:
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            if row.get("name"):
                records.append(row)

    if not records:
        return jsonify({
            "code": 400, "msg": "No valid records found in file",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    if len(records) > 10000:
        return jsonify({
            "code": 400, "msg": "Maximum 10000 records per import",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    db = _get_company_db()
    result = db.import_batch(records)

    return jsonify({
        "code": 200,
        "data": result,
        "requestId": getattr(g, "request_id", "-"),
    })
