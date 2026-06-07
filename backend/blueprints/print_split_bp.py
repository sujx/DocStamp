"""Print split routes."""

import os
import uuid

from flask import Blueprint, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.print_split import split_pdf

print_split_bp = Blueprint("print_split", __name__)

_tasks = {}


@print_split_bp.route("/api/print-split", methods=["POST"])
def print_split_create():
    filepath = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        batch_size = int(request.form.get("batch_size", 60))
        interval_seconds = int(request.form.get("interval", 60))

        if batch_size < 1:
            return jsonify({"error": _("Batch size must be at least 1")}), 400
        if interval_seconds < 0:
            return jsonify({"error": _("Interval must be non-negative")}), 400

        task_id = uuid.uuid4().hex[:12]
        task_dir = os.path.join(Config.UPLOAD_FOLDER, task_id)
        os.makedirs(task_dir, exist_ok=True)
        result = split_pdf(filepath, task_dir, batch_size)
        if not result.success:
            cleanup_files(filepath)
            return jsonify({"error": result.message}), 400

        batches = result.data
        _tasks[task_id] = {"task_dir": task_dir, "batches": batches, "filepath": filepath}

        return jsonify({
            "success": True,
            "task_id": task_id,
            "total_pages": sum(b["pages"] for b in batches),
            "batch_count": len(batches),
            "batches": batches,
        })
    except ValueError as e:
        cleanup_files(filepath)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath)
        return jsonify({"error": str(e)}), 500


@print_split_bp.route("/api/print-split/<task_id>/batch/<int:batch_no>", methods=["GET"])
def print_split_download(task_id: str, batch_no: int):
    try:
        if task_id not in _tasks:
            return jsonify({"error": _("Task not found")}), 404
        task = _tasks[task_id]
        batches = task["batches"]
        if batch_no < 1 or batch_no > len(batches):
            return jsonify({"error": _("Invalid batch number")}), 400
        batch = batches[batch_no - 1]
        batch_file = os.path.join(task["task_dir"], batch["filename"])
        if not os.path.isfile(batch_file):
            return jsonify({"error": _("Batch file not found")}), 404
        return send_file(batch_file, mimetype="application/pdf", as_attachment=True, download_name=batch["filename"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
