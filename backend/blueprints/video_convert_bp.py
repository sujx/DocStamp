"""Video conversion blueprint: MP4 → WMV for PowerPoint embedding."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.video_converter import mp4_to_wmv

video_convert_bp = Blueprint("video-convert", __name__)


@video_convert_bp.route("/api/v1/video-convert", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def video_convert():
    """Convert uploaded video to WMV format.

    Returns the converted .wmv file as a download.
    """
    filepath = None
    output_path = None

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        filename, filepath = save_upload(
            file, Config.VIDEO_EXTENSIONS, Config.UPLOAD_FOLDER
        )

        # Output file — same name but .wmv extension
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        output_name = f"{uuid.uuid4().hex}_{base}.wmv"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)

        result = mp4_to_wmv(filepath, output_path)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        download_name = f"{base}.wmv"

        return send_file(
            output_path,
            mimetype="video/x-ms-wmv",
            as_attachment=True,
            download_name=download_name,
        )

    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
