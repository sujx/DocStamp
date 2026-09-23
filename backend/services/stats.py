"""Stats aggregation service — business logic extracted from stats_bp.

Provides module-level aggregation, daily trends, unique visitor counts,
and test-data seeding for the stats dashboard.
"""

import random
from datetime import datetime, timedelta, timezone

from config import Config
from backend.models import OperationLog

MODULE_NAMES = {
    "convert": "MD 转公文",
    "properties": "属性修改",
    "img2pdf": "图片合 PDF",
    "pdf2img": "PDF 拆图",
    "print-split": "打印分组",
    "pdf-editor": "PDF 编辑",
    "excel-merge": "Excel 合并",
    "pdf-to-text": "PDF 转文本",
    "pdf-merge": "PDF 合并",
    "pdf-compress": "PDF 压缩",
    "metadata-clean": "清理元数据",
    "page-decorate": "页码页眉",
    "format-docx": "格式规范",
    "pageview": "页面浏览",
}

_op_log = None


def _get_op_log() -> OperationLog:
    global _op_log
    if _op_log is None:
        _op_log = OperationLog(Config.TASK_DB_PATH)
    return _op_log


def aggregate_by_module(since: str) -> list[dict]:
    op_log = _get_op_log()
    try:
        raw = op_log._by_module(since)
    except Exception:
        raw = []

    by_module = []
    for r in raw:
        module = r.get("operation_type", "unknown")
        if module not in MODULE_NAMES:
            continue
        by_module.append({
            "module": module,
            "label": MODULE_NAMES[module],
            "count": r.get("cnt", 0),
        })
    by_module.sort(key=lambda x: x["count"], reverse=True)
    return by_module


def daily_trend(since: str, days: int) -> list[dict]:
    op_log = _get_op_log()
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


def unique_visitors(since: str) -> int:
    op_log = _get_op_log()
    try:
        return op_log._count_distinct_ips(since)
    except Exception:
        return 0


def build_overview(days: int) -> dict:
    days = max(1, min(days, 365))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    by_module = aggregate_by_module(since)
    total = sum(m["count"] for m in by_module)

    return {
        "total": total,
        "by_module": by_module,
        "daily_trend": daily_trend(since, days),
        "unique_visitors": unique_visitors(since),
        "days": days,
    }


def seed_test_data() -> dict:
    op_log = _get_op_log()
    existing = op_log._count_all()
    if existing > 30:
        return {"seeded": 0, "skipped": True, "existing": existing}

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
    modules = list(MODULE_NAMES.keys())
    now = datetime.now(timezone.utc)

    seeded = 0
    for module in modules:
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

    return {"seeded": seeded, "skipped": False, "modules": modules}
