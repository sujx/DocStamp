"""Stats dashboard routes: /api/stats/overview"""

import random
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, g, request

from config import Config
from models import OperationLog

stats_bp = Blueprint("stats", __name__)

_op_log = None


def _get_op_log():
    global _op_log
    if _op_log is None:
        _op_log = OperationLog(Config.TASK_DB_PATH)
    return _op_log


# ── Module display names (i18n-friendly) ──────────────────────────────

MODULE_NAMES = {
    "convert": "MD 转公文",
    "properties": "属性修改",
    "img2pdf": "图片合 PDF",
    "pdf2img": "PDF 拆图",
    "print-split": "打印分组",
    "watermark": "水印管理",
    "pdf-editor": "PDF 编辑",
    "excel-merge": "Excel 合并",
    "pdf-to-text": "PDF 转文本",
    "pdf-merge": "PDF 合并",
    "pdf-compress": "PDF 压缩",
    "metadata-clean": "清理元数据",
    "page-decorate": "页码页眉",
    "doc-to-md": "文档转MD",
    "format-docx": "格式规范",
    "video-convert": "视频转换",
    "pageview": "页面浏览",
}


@stats_bp.route("/sitemap.xml")
def sitemap():
    """Generate sitemap for all tool pages."""
    pages = [
        "",  # home
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
    from flask import Response
    return Response(xml, mimetype="application/xml")


@stats_bp.route("/api/v1/track", methods=["POST"])
def track_pageview():
    """Record a page view.  Frontend sends {page: 'video-convert'} on each nav.

    No auth required — lightweight beacon, swallowed silently on failure.
    """
    try:
        op_log = _get_op_log()
        data = request.get_json(silent=True) or {}
        page = (data.get("page") or "/").strip()[:100]
        op_log.log_operation(
            session_id=getattr(g, "request_id", "-"),
            operation_type="pageview",
            resource_id=page,
            resource_type="pv",
            ip_address=(request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                        or request.headers.get("X-Real-IP", "")
                        or request.remote_addr
                        or ""),
            user_agent=(request.user_agent.string or "")[:200],
            status="success",
        )
    except Exception:
        pass  # Never break on analytics
    return jsonify({"ok": True})


@stats_bp.route("/api/v1/stats/overview", methods=["GET"])
def stats_overview():
    """Aggregate operation counts by module, daily trend, and unique visitors.

    Query params:
        days  – lookback window in days (default 30)
    """
    try:
        days = int(request.args.get("days", "30"))
    except (ValueError, TypeError):
        days = 30
    days = max(1, min(days, 365))

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    op_log = _get_op_log()

    # ── By module ────────────────────────────────────────────────────
    try:
        raw = op_log._by_module(since)
    except Exception:
        # Fallback to a generic list-by-time approach
        raw = []

    by_module = []
    for r in raw:
        module = r.get("operation_type", "unknown")
        by_module.append({
            "module": module,
            "label": MODULE_NAMES.get(module, module),
            "count": r.get("cnt", 0),
        })
    by_module.sort(key=lambda x: x["count"], reverse=True)

    # ── Daily trend (last N days) ─────────────────────────────────────
    daily = _daily_trend(op_log, since, days)

    # ── Unique visitors (distinct IPs) ────────────────────────────────
    visitors = _unique_visitors(op_log, since)

    # ── Total calls ───────────────────────────────────────────────────
    total = sum(m["count"] for m in by_module)

    return jsonify({
        "code": 200,
        "data": {
            "total": total,
            "by_module": by_module,
            "daily_trend": daily,
            "unique_visitors": visitors,
            "days": days,
        },
        "requestId": getattr(g, "request_id", "-"),
    })


# ── Seed test data ──────────────────────────────────────────────────────────

MODULES = list(MODULE_NAMES.keys())


@stats_bp.route("/api/v1/stats/seed", methods=["POST"])
def seed_test_data():
    """Insert random test data (≤10 records per module) for demo purposes.

    This endpoint is safe to call multiple times — it only seeds if the
    operation_logs table has fewer than 30 total rows already, so it won't
    flood a production database.
    """
    op_log = _get_op_log()
    existing = op_log._count_all()
    if existing > 30:
        return jsonify({
            "code": 200,
            "msg": f"Already has {existing} operation logs; skipping seed.",
        })

    test_ips = [
        "192.168.1.10", "10.0.0.5", "172.16.0.23",
        "192.168.1.20", "10.0.0.8", "127.0.0.1",
    ]
    test_agents = [
        "Mozilla/5.0 Chrome/120.0",
        "Mozilla/5.0 Safari/17.0",
        "Mozilla/5.0 Firefox/120.0",
        "Mozilla/5.0 Edge/120.0",
    ]
    now = datetime.now(timezone.utc)

    seeded = 0
    for module in MODULES:
        records = random.randint(1, 10)
        for i in range(records):
            ts = (now - timedelta(
                days=random.randint(0, 14),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )).isoformat()
            op_log.log_operation(
                session_id=f"seed-{module}-{i}",
                operation_type=module,
                resource_id=f"/api/v1/{module}",
                resource_type="",
                ip_address=random.choice(test_ips),
                user_agent=random.choice(test_agents),
                status=random.choices(["success", "error"], weights=[0.9, 0.1])[0],
                duration_ms=random.randint(50, 5000),
            )
            seeded += 1

    return jsonify({
        "code": 200,
        "msg": f"Seeded {seeded} test records across {len(MODULES)} modules",
        "modules": MODULES,
    })


# ── Helpers ────────────────────────────────────────────────────────────────

def _daily_trend(op_log, since: str, days: int) -> list[dict]:
    """Return per-day call counts for the last N days, zero-filling gaps."""
    try:
        rows = op_log._daily_counts(since)
    except Exception:
        rows = []

    by_date = {r.get("date", ""): r.get("cnt", 0) for r in rows}

    result = []
    today = datetime.now(timezone.utc).date()
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        result.append({"date": d, "count": by_date.get(d, 0)})
    return result


def _unique_visitors(op_log, since: str) -> int:
    """Count distinct IPs since the given timestamp."""
    try:
        return op_log._count_distinct_ips(since)
    except Exception:
        return 0
