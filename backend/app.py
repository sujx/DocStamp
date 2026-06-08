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

    # Register blueprints — one per feature for clear module boundaries
    from blueprints.convert import convert_bp
    from blueprints.download import download_bp
    from blueprints.properties_bp import properties_bp
    from blueprints.img2pdf_bp import img2pdf_bp
    from blueprints.pdf2img_bp import pdf2img_bp
    from blueprints.print_split_bp import print_split_bp
    from blueprints.watermark_bp import watermark_bp
    from blueprints.pdf_editor_bp import pdf_editor_bp
    from blueprints.excel_merge_bp import excel_merge_bp
    from blueprints.pdf_to_text_bp import pdf_to_text_bp
    from blueprints.pdf_merge_bp import pdf_merge_bp

    app.register_blueprint(convert_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(img2pdf_bp)
    app.register_blueprint(pdf2img_bp)
    app.register_blueprint(print_split_bp)
    app.register_blueprint(watermark_bp)
    app.register_blueprint(pdf_editor_bp)
    app.register_blueprint(excel_merge_bp)
    app.register_blueprint(pdf_to_text_bp)
    app.register_blueprint(pdf_merge_bp)

    from blueprints.pdf_compress_bp import pdf_compress_bp
    from blueprints.metadata_clean_bp import metadata_clean_bp
    from blueprints.format_convert_bp import format_convert_bp
    from blueprints.page_decorate_bp import page_decorate_bp
    from blueprints.image_process_bp import image_process_bp

    app.register_blueprint(pdf_compress_bp)
    app.register_blueprint(metadata_clean_bp)
    app.register_blueprint(format_convert_bp)
    app.register_blueprint(page_decorate_bp)
    app.register_blueprint(image_process_bp)

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
