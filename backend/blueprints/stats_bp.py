"""Stats dashboard routes: /api/stats/overview, /api/v1/track, sitemap."""

from flask import Blueprint, Response, g, jsonify, request

from services import stats as stats_service

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/sitemap.xml")
def sitemap():
    pages = [
        "",
        "/md-to-docx", "/doc-to-md", "/format-docx",
        "/watermark", "/video-convert",
        "/properties", "/excel-merge",
        "/file-assembly", "/print-split", "/pdf-editor",
        "/pdf-tools", "/pdf-merge", "/status",
    ]
    base = request.host_url.rstrip("/")
    items = "\n".join(
        f"  <url><loc>{base}{p}</loc><changefreq>monthly</changefreq><priority>{'1.0' if p == '' else '0.8'}</priority></url>"
        for p in pages
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>'
    return Response(xml, mimetype="application/xml")


@stats_bp.route("/api/v1/track", methods=["POST"])
def track_pageview():
    from flask import request as req
    try:
        from backend.models import OperationLog
        from config import Config
        op_log = OperationLog(Config.TASK_DB_PATH)
        data = req.get_json(silent=True) or {}
        page = (data.get("page") or "/").strip()[:100]
        op_log.log_operation(
            session_id=getattr(g, "request_id", "-"),
            operation_type="pageview",
            resource_id=page,
            resource_type="pv",
            ip_address=(req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                        or req.headers.get("X-Real-IP", "")
                        or req.remote_addr
                        or ""),
            user_agent=(req.user_agent.string or "")[:200],
            status="success",
        )
    except Exception:
        pass
    return jsonify({"ok": True})


@stats_bp.route("/api/v1/stats/overview", methods=["GET"])
def stats_overview():
    try:
        days = int(request.args.get("days", "30"))
    except (ValueError, TypeError):
        days = 30

    data = stats_service.build_overview(days)
    return jsonify({
        "code": 200,
        "data": data,
        "requestId": getattr(g, "request_id", "-"),
    })


@stats_bp.route("/api/v1/stats/seed", methods=["POST"])
def seed_test_data():
    result = stats_service.seed_test_data()
    if result["skipped"]:
        return jsonify({
            "code": 200,
            "msg": f"Already has {result['existing']} operation logs; skipping seed.",
        })
    return jsonify({
        "code": 200,
        "msg": f"Seeded {result['seeded']} test records across {len(result['modules'])} modules",
        "modules": result["modules"],
    })
