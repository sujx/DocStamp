"""Page Decorator routes — page numbers, headers, footers."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.page_decorator import add_page_numbers

page_decorate_bp = Blueprint("page_decorate", __name__)


@page_decorate_bp.route("/api/v1/page-decorate", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def page_decorate():
    """Add page numbers, headers, or footers to a PDF."""
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)

        params_str = request.form.get("params", "{}")
        try:
            params = json.loads(params_str)
        except (json.JSONDecodeError, TypeError):
            params = {}

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = add_page_numbers(filepath, output_path, params)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=f"decorated_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
