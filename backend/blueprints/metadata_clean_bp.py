"""Metadata Cleaner routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.metadata_cleaner import clean_metadata

METADATA_CLEAN_EXTENSIONS = {"docx", "xlsx", "pptx", "pdf"}

metadata_clean_bp = Blueprint("metadata_clean", __name__)


@metadata_clean_bp.route("/api/metadata-clean", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def metadata_clean():
    """Strip all metadata from an Office or PDF file."""
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, METADATA_CLEAN_EXTENSIONS, Config.UPLOAD_FOLDER)

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = clean_metadata(filepath, output_path)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        response = send_file(output_path, as_attachment=True, download_name=f"cleaned_{filename}")
        response.headers["X-Fields-Cleaned"] = str(result.data.get("fields_cleaned", 0))
        return response
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
