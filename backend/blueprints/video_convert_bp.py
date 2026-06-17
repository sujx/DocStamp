"""Video conversion blueprint: MP4 → WMV (async via Celery)."""

import os
import uuid

from flask import Blueprint, jsonify, request

from config import Config
from utils.base.file_helpers import save_upload
from utils.rate_limit import rate_limit

video_convert_bp = Blueprint("video-convert", __name__)


@video_convert_bp.route("/api/v1/video-convert", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def video_convert():
    """Start async video conversion. Returns task_id for SSE progress tracking."""
    filepath = None

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        filename, filepath = save_upload(
            file, Config.VIDEO_EXTENSIONS, Config.UPLOAD_FOLDER
        )

        # Output will be created by the Celery task
        output_name = f"{uuid.uuid4().hex}.wmv"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)

        from backend.tasks.video import video_convert_async
        task = video_convert_async.delay(filepath, output_path, filename)

        return jsonify({
            "success": True,
            "task_id": task.id,
            "message": "Video conversion started",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
