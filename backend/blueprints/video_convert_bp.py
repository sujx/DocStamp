"""Video conversion blueprint: MP4 → WMV (queued for the task worker)."""

import json
import uuid

from flask import Blueprint, jsonify, request

from config import Config
from models import TaskRecord
from utils.base.file_helpers import save_upload
from utils.rate_limit import rate_limit

video_convert_bp = Blueprint("video-convert", __name__)


@video_convert_bp.route("/api/v1/video-convert", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def video_convert():
    """Start async video conversion. Returns task_id for SSE progress tracking."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        input_name, _filepath = save_upload(
            file, Config.VIDEO_EXTENSIONS, Config.UPLOAD_FOLDER
        )

        task_id = uuid.uuid4().hex
        # Only basenames are queued: api and worker share the upload volume, so
        # each side resolves them against its own Config.UPLOAD_FOLDER.
        TaskRecord(Config.TASK_DB_PATH).create_task(
            task_id, "video_convert", "pdf_queue",
            result_data=json.dumps({
                "input": input_name,
                "output": f"{task_id}.wmv",
            }),
        )

        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "Video conversion started",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
