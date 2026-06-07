"""Image Processing routes — resize, crop, convert, compress."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.image_processor import process_image

IMAGE_PROCESS_EXTENSIONS = {"png", "jpg", "jpeg", "tiff", "tif", "webp"}

image_process_bp = Blueprint("image_process", __name__)


@image_process_bp.route("/api/image-process", methods=["POST"])
def image_process():
    """Resize, crop, convert, or compress an image."""
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, IMAGE_PROCESS_EXTENSIONS, Config.UPLOAD_FOLDER)

        params_str = request.form.get("params", "{}")
        try:
            params = json.loads(params_str)
        except (json.JSONDecodeError, TypeError):
            params = {}

        ext = os.path.splitext(filename)[1]
        output_name = f"{uuid.uuid4().hex}{ext}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = process_image(filepath, output_path, params)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"processed_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
