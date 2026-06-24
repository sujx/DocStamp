"""Company name → website lookup blueprint.

Three endpoints:
    POST /api/v1/company-lookup        — single synchronous lookup
    POST /api/v1/company-lookup/batch  — batch async lookup (Celery + SSE)
    POST /api/v1/company-lookup/confirm — confirm and save to local DB
"""

from flask import Blueprint, g, jsonify, request

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
    """Start an async batch company lookup.

    Returns a task_id for SSE progress streaming via
    /api/v1/tasks/{task_id}/stream.
    """
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

    # Trim and filter empty names
    names = [n.strip() for n in names if n and n.strip()]
    if not names:
        return jsonify({
            "code": 400, "msg": "No valid company names provided",
            "requestId": getattr(g, "request_id", "-"),
        }), 400

    from backend.tasks.lookup import company_lookup_batch as batch_task
    task = batch_task.delay(names)

    return jsonify({
        "code": 200,
        "data": {"task_id": task.id, "total": len(names)},
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
