"""Download and health endpoints."""

import mimetypes
import os

from flask import Blueprint, Response, jsonify, request, send_file
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from config import Config
from utils.base.file_helpers import safe_download_name

download_bp = Blueprint("download", __name__)


# ── Helpers ─────────────────────────────────────────────────────────

def _parse_range(range_header: str, file_size: int) -> tuple:
    try:
        unit, ranges = range_header.split("=")
        if unit != "bytes":
            raise ValueError
        start_str, end_str = ranges.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        return start, end
    except (ValueError, AttributeError):
        return 0, file_size - 1


# ── Routes ──────────────────────────────────────────────────────────

@download_bp.route("/api/v1/health", methods=["GET"])
def health():
    import shutil
    deps = {
        "pandoc": shutil.which("pandoc") is not None,
    }
    return jsonify({"status": "ok", "deps": deps})


@download_bp.route("/api/v1/download/<filename>")
def download_file(filename: str):
    """Serve a generated file with Range request support."""
    for char in Config.FORBIDDEN_PATH_CHARS:
        if char in filename:
            return jsonify({"error": _("Invalid filename")}), 400
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in Config.DOWNLOAD_EXTENSIONS:
        return jsonify({"error": _("File type not allowed for download")}), 400
    safe_name = secure_filename(filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, safe_name)
    if not os.path.isfile(filepath):
        return jsonify({"error": _("File not found")}), 404

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("Range")
    mimetype = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    if ext == "md":
        mimetype = "text/markdown; charset=utf-8"

    if range_header:
        start, end = _parse_range(range_header, file_size)
        length = end - start + 1
        with open(filepath, "rb") as f:
            f.seek(start)
            chunk = f.read(length)
        response = Response(chunk, 206, mimetype=mimetype)
        response.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Length"] = str(length)
    else:
        response = send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=safe_download_name(safe_name))
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Length"] = str(file_size)
    return response
