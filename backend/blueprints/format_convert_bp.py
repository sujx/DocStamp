"""Format Conversion routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.format_converter import convert_document

CONVERT_EXTENSIONS = {"docx", "html", "htm"}

format_convert_bp = Blueprint("format_convert", __name__)


@format_convert_bp.route("/api/convert/format", methods=["POST"])
def format_convert():
    """Convert a document between formats (DOCX→PDF, HTML→PDF)."""
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, CONVERT_EXTENSIONS, Config.UPLOAD_FOLDER)
        target_format = request.form.get("target_format", "pdf")

        ext = os.path.splitext(filename)[1].lower()
        output_name = f"{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = convert_document(filepath, output_path, target_format)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        download_name = os.path.splitext(filename)[0] + ".pdf"

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=download_name)
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
