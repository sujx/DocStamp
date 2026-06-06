"""Flask REST API for docStamp Document Processing Toolbox.

Thin factory: creates Flask instance, registers blueprints, configures middleware.
All route logic lives in blueprints/ — business logic in services/.
"""

import os
from flask import Flask, g, jsonify, request, send_from_directory
from flask_babel import Babel
from flask_cors import CORS

from config import Config
from json_logging import setup_json_logging
from error_handler import register_error_handlers
from cache import init_cache
from models import init_db


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # i18n
    def get_locale():
        return request.accept_languages.best_match(
            app.config.get("LANGUAGES", ["en", "zh_CN"]), default="en"
        )

    Babel(app, default_locale="en", locale_selector=get_locale)
    CORS(app)

    # Infrastructure
    setup_json_logging(app)
    register_error_handlers(app)
    init_cache(app)
    init_db(app.config["TASK_DB_PATH"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    from blueprints.convert import convert_bp
    from blueprints.files import files_bp
    from blueprints.download import download_bp

    app.register_blueprint(convert_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(download_bp)

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

        # SPA fallback — return root index.html for all unmatched routes
        if os.path.isfile(os.path.join(static_dir, "index.html")):
            return send_from_directory(static_dir, "index.html")

        return jsonify({
            "code": 503, "msg": "Frontend index.html not found",
            "requestId": getattr(g, "request_id", "-"),
        }), 503

    app.logger.info("docStamp application initialized")
    return app


# ── Entry point ─────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
