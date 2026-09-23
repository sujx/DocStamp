"""WebP to JPEG conversion routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, safe_download_name, save_upload
from utils.rate_limit import rate_limit
from services.webp_to_jpeg import webp_to_jpeg

webp_to_jpeg_bp = Blueprint("webp_to_jpeg", __name__)

WEBP_EXTENSIONS = {"webp"}


@webp_to_jpeg_bp.route("/api/v1/webp-to-jpeg", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def webp_to_jpeg_convert():
    input_path = None
    output_path = None
    try:
        f = request.files.get("file")
        if f is None or not f.filename:
            return jsonify({"error": _("No file provided")}), 400

        _name, input_path = save_upload(f, WEBP_EXTENSIONS, Config.UPLOAD_FOLDER)

        output_path = os.path.join(Config.UPLOAD_FOLDER, f"{uuid.uuid4().hex}.jpg")
        result = webp_to_jpeg(input_path, output_path)
        if not result.success:
            cleanup_files(input_path, output_path)
            return jsonify({"error": result.message}), 400

        stem = safe_download_name(os.path.splitext(f.filename)[0])

        @after_this_request
        def _cleanup(response):
            cleanup_files(input_path, output_path)
            return response

        return send_file(
            output_path,
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=f"{stem}.jpg",
        )
    except ValueError as e:
        cleanup_files(input_path, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(input_path, output_path)
        return jsonify({"error": str(e)}), 500
