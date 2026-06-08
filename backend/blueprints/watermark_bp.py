"""Watermark addition and removal routes."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.watermark import add_watermark, remove_watermark

watermark_bp = Blueprint("watermark", __name__)


@watermark_bp.route("/api/watermark", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def watermark_add():
    filepath = None
    image_path = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.WATERMARK_EXTENSIONS, Config.UPLOAD_FOLDER)

        params_str = request.form.get("params", "{}")
        try:
            params = json.loads(params_str)
        except (json.JSONDecodeError, TypeError):
            params = {}

        watermark_type = params.get("watermark_type", "text")
        if watermark_type == "text" and not params.get("text", ""):
            return jsonify({"error": _("Watermark text is required")}), 400
        elif watermark_type == "image":
            if "watermark_image" not in request.files:
                return jsonify({"error": _("Watermark image is required")}), 400
            img_file = request.files["watermark_image"]
            if img_file.filename:
                image_name, image_path = save_upload(img_file, Config.IMAGE_EXTENSIONS, Config.UPLOAD_FOLDER)

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = add_watermark(filepath, output_path, params, image_path)
        if not result.success:
            cleanup_files(filepath, output_path, image_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path, image_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"watermarked_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path, image_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path, image_path)
        return jsonify({"error": str(e)}), 500


@watermark_bp.route("/api/watermark/remove", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def watermark_remove():
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.WATERMARK_EXTENSIONS, Config.UPLOAD_FOLDER)
        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = remove_watermark(filepath, output_path)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"cleaned_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
