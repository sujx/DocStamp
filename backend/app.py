"""Flask REST API for docStamp Document Processing Toolbox.

Thin factory: creates Flask instance, registers blueprints, configures middleware.
All route logic lives in blueprints/ — business logic in services/.
"""

import os
import sys
import time

# Ensure the project root is on sys.path so that `from backend.xxx`
# imports resolve correctly regardless of working directory (dev mode
# runs as `python3 app.py` from backend/; gunicorn does the same).
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Load .env before any config reads — works regardless of startup method
# (gunicorn, python app.py, systemd).  Searches project root and backend/.
for _dotenv_path in (".env", "../.env"):
    if os.path.isfile(_dotenv_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(_dotenv_path)
        except ImportError:
            pass  # python-dotenv not installed, rely on shell env
        break
from flask import Flask, g, jsonify, request, send_from_directory
from flask_babel import Babel
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from json_logging import setup_json_logging
from error_handler import register_error_handlers
from cache import init_cache
from models import OperationLog, init_db


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Trust one reverse-proxy hop (nginx) so request.remote_addr / scheme / host
    # reflect the real client. Per-IP rate limiting silently degrades to a single
    # shared bucket without this.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # i18n
    def get_locale():
        return request.accept_languages.best_match(
            app.config.get("LANGUAGES", ["en", "zh_CN"]), default="en"
        )

    Babel(app, default_locale="en", locale_selector=get_locale)
    CORS(
        app,
        origins=os.environ.get(
            "DOCSTAMP_CORS_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080",
        ).split(","),
        max_age=3600,
    )

    # Infrastructure
    setup_json_logging(app)
    register_error_handlers(app)
    init_cache(app)
    init_db(app.config["TASK_DB_PATH"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Operation-logging middleware ──────────────────────────────────
    # Auto-log every /api/* call to operation_logs so the status
    # dashboard can show per-module usage + visitor counts.
    _op_log = None

    def _get_op_log():
        nonlocal _op_log
        if _op_log is None:
            _op_log = OperationLog(app.config["TASK_DB_PATH"])
        return _op_log

    @app.before_request
    def _start_op_timer():
        if request.path.startswith("/api/") and request.path != "/api/health":
            g._op_start = time.time()

    @app.after_request
    def _set_version_header(response):
        response.headers["X-API-Version"] = "3.7"
        return response

    @app.after_request
    def _commit_op_log(response):
        start = getattr(g, "_op_start", None)
        if start is None:
            return response

        # Extract a short module name from the URL path
        # e.g. /api/v1/pdf-editor/info → "pdf-editor", /api/v1/convert → "convert"
        path = request.path
        parts = [p for p in path.split("/") if p]
        # Skip /api/v1/ prefix — parts[0]="api", parts[1]="v1", parts[2]=<module>
        module = parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 else "unknown")

        duration_ms = int((time.time() - start) * 1000)
        success = 200 <= response.status_code < 400

        try:
            _get_op_log().log_operation(
                session_id=getattr(g, "request_id", "-"),
                operation_type=module,
                resource_id=path,
                resource_type=parts[2] if len(parts) > 2 else "",
                # Behind nginx proxy, remote_addr is always 127.0.0.1.
                # Read real client IP from X-Forwarded-For (leftmost is client).
                ip_address=(request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                            or request.headers.get("X-Real-IP", "")
                            or request.remote_addr
                            or ""),
                user_agent=(request.user_agent.string or "")[:200],
                status="success" if success else "error",
                duration_ms=duration_ms,
            )
        except Exception:
            pass  # Logging must never break the response

        return response

    # Register blueprints — one per feature for clear module boundaries
    from blueprints.convert import convert_bp
    from blueprints.download import download_bp
    from blueprints.properties_bp import properties_bp
    from blueprints.img2pdf_bp import img2pdf_bp
    from blueprints.pdf2img_bp import pdf2img_bp
    from blueprints.print_split_bp import print_split_bp
    from blueprints.pdf_editor_bp import pdf_editor_bp
    from blueprints.excel_merge_bp import excel_merge_bp
    from blueprints.pdf_to_text_bp import pdf_to_text_bp
    from blueprints.pdf_merge_bp import pdf_merge_bp
    from blueprints.webp_to_jpeg_bp import webp_to_jpeg_bp
    from blueprints.pdf_redact_bp import pdf_redact_bp

    app.register_blueprint(convert_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(img2pdf_bp)
    app.register_blueprint(pdf2img_bp)
    app.register_blueprint(print_split_bp)
    app.register_blueprint(pdf_editor_bp)
    app.register_blueprint(excel_merge_bp)
    app.register_blueprint(pdf_to_text_bp)
    app.register_blueprint(pdf_merge_bp)
    app.register_blueprint(webp_to_jpeg_bp)
    app.register_blueprint(pdf_redact_bp)

    from blueprints.pdf_compress_bp import pdf_compress_bp
    from blueprints.metadata_clean_bp import metadata_clean_bp
    from blueprints.page_decorate_bp import page_decorate_bp
    from blueprints.stats_bp import stats_bp
    from blueprints.rss_detect_bp import rss_detect_bp

    app.register_blueprint(pdf_compress_bp)
    app.register_blueprint(metadata_clean_bp)
    app.register_blueprint(page_decorate_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(rss_detect_bp)

    # SPA fallback — serve frontend static files (Nuxt generate output)
    static_dir = app.config["STATIC_FOLDER"]

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        if not os.path.isdir(static_dir):
            return jsonify({
                "code": 503, "msg": "Frontend not built. Run 'npm run build' in frontend/.",
                "requestId": getattr(g, "request_id", "-"),
            }), 503

        # Try exact file match (e.g. /logo.svg, /_nuxt/app.js)
        full_path = os.path.join(static_dir, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(static_dir, path)

        # Try directory with index.html (Nuxt generate: /md-to-docx/index.html)
        if path and os.path.isdir(full_path):
            dir_index = os.path.join(full_path, "index.html")
            if os.path.isfile(dir_index):
                return send_from_directory(static_dir, os.path.join(path, "index.html"))

        # Before falling back to index.html, check if the request looks like
        # a static asset (has a file extension).  If so, return 404 instead
        # of index.html — otherwise the browser receives HTML when it expects
        # JS/CSS and throws MIME-type errors (e.g. stale _nuxt/*.js hashes).
        if path and "." in path.rsplit("/", 1)[-1]:
            return jsonify({
                "code": 404, "msg": "Asset not found",
                "requestId": getattr(g, "request_id", "-"),
            }), 404

        # SPA fallback — return root index.html for all unmatched routes
        if os.path.isfile(os.path.join(static_dir, "index.html")):
            return send_from_directory(static_dir, "index.html")

        return jsonify({
            "code": 503, "msg": "Frontend index.html not found",
            "requestId": getattr(g, "request_id", "-"),
        }), 503

    app.logger.info("docStamp application initialized")
    return app


# ── Entry points ────────────────────────────────────────────────────
# Production: Gunicorn calls `backend.wsgi:app` where wsgi.py does
#   `from app import create_app; app = create_app()`
# Development: `python3 app.py` triggers the block below.
# NEVER import this module at module level — use create_app() factory.

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
