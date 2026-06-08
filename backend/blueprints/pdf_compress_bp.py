"""PDF Compression routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.pdf_compressor import compress_pdf

pdf_compress_bp = Blueprint("pdf_compress", __name__)


@pdf_compress_bp.route("/api/pdf-compress", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def pdf_compress():
    """Compress a PDF file."""
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        quality = request.form.get("quality", "medium")

        output_name = f"{uuid.uuid4().hex}_compressed.pdf"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = compress_pdf(filepath, output_path, quality)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        resp = send_file(
            output_path, mimetype="application/pdf", as_attachment=True,
            download_name=f"compressed_{filename}",
        )
        resp.headers["X-Original-Size"] = str(result.data["original_size"])
        resp.headers["X-Compressed-Size"] = str(result.data["compressed_size"])
        resp.headers["X-Compression-Ratio"] = str(result.data["ratio"])
        return resp
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
