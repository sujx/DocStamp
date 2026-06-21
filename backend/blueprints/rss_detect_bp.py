"""RSS feed detection blueprint."""

from flask import Blueprint, g, jsonify, request

from utils.rate_limit import rate_limit
from services.rss_detector import detect_feeds

rss_detect_bp = Blueprint("rss-detect", __name__)


@rss_detect_bp.route("/api/v1/rss-detect", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def rss_detect():
    """Detect RSS/Atom feeds for a given URL."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"code": 400, "msg": "URL is required", "requestId": getattr(g, "request_id", "-")}), 400

    result = detect_feeds(url)
    if not result.success:
        return jsonify({"code": 400, "msg": result.message, "requestId": getattr(g, "request_id", "-")}), 400

    return jsonify({
        "code": 200,
        "data": {"url": url, "feeds": result.data},
        "requestId": getattr(g, "request_id", "-"),
    })
