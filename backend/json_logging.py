"""JSON structured logging with timed rotation.

Features:
- One JSON object per log line (grep/jq/ELK compatible)
- requestId propagation from Flask g to log records
- Daily rotation with 30-day retention
- Automatic stack trace capture on exceptions
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, g, has_request_context

LOG_DIR = "/var/log/docstamp"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB (fallback size-based rotation)
LOG_BACKUP_COUNT = 30  # Keep 30 daily files


# ── Request-Aware Filter ────────────────────────────────────────────────

class RequestIdFilter(logging.Filter):
    """Inject requestId into every log record when inside a Flask request."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.requestId = getattr(g, "request_id", "-") if has_request_context() else "-"
        return True


# ── JSON Formatter ──────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "requestId": getattr(record, "requestId", "-"),
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["stack"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ── Setup ───────────────────────────────────────────────────────────────

def setup_json_logging(app: Flask) -> None:
    """Configure JSON-structured logging with daily rotation.

    Should be called once during create_app(), before any routes are registered.

    Logs are written to:
        /var/log/docstamp/app.log       (current)
        /var/log/docstamp/app.log.YYYY-MM-DD  (rotated, kept 30 days)
        /var/log/docstamp/error.log     (errors, same rotation)
    """
    app.logger.setLevel(app.config.get("LOG_LEVEL", logging.INFO))
    app.logger.handlers.clear()

    # Console handler (stderr, for development)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if app.debug else logging.WARNING)
    console.setFormatter(JsonFormatter())
    console.addFilter(RequestIdFilter())
    app.logger.addHandler(console)

    # File handler (daily rotation, 30-day retention)
    try:
        os.makedirs(LOG_DIR, mode=0o755, exist_ok=True)

        app_handler = TimedRotatingFileHandler(
            os.path.join(LOG_DIR, "app.log"),
            when="midnight",
            interval=1,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        app_handler.setLevel(app.config.get("LOG_LEVEL", logging.INFO))
        app_handler.setFormatter(JsonFormatter())
        app_handler.addFilter(RequestIdFilter())
        app.logger.addHandler(app_handler)

        error_handler = TimedRotatingFileHandler(
            os.path.join(LOG_DIR, "error.log"),
            when="midnight",
            interval=1,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JsonFormatter())
        error_handler.addFilter(RequestIdFilter())
        app.logger.addHandler(error_handler)

        app.logger.info("JSON logging initialized: %s", LOG_DIR)

    except (OSError, PermissionError) as e:
        app.logger.warning(
            "Cannot write to %s (%s), logging to stderr only", LOG_DIR, e
        )
