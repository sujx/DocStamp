"""Image to PDF merge routes."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.img2pdf_handler import images_to_pdf

img2pdf_bp = Blueprint("img2pdf", __name__)


@img2pdf_bp.route("/api/img2pdf", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def img2pdf_merge():
    image_paths = []
    output_path = None
    try:
        if "files" not in request.files:
            return jsonify({"error": _("No files provided")}), 400
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            return jsonify({"error": _("No files selected")}), 400

        for f in files:
            if f.filename:
                _name, path = save_upload(f, Config.IMAGE_EXTENSIONS, Config.UPLOAD_FOLDER)
                image_paths.append(path)
        if not image_paths:
            return jsonify({"error": _("No valid images uploaded")}), 400

        order_str = request.form.get("order", "[]")
        try:
            order = json.loads(order_str)
        except (json.JSONDecodeError, TypeError):
            order = list(range(len(image_paths)))

        sorted_paths = [image_paths[i] for i in order] if order and len(order) == len(image_paths) else image_paths
        page_size = request.form.get("page_size", "original")

        output_name = f"{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = images_to_pdf(sorted_paths, output_path, page_size)
        if not result.success:
            for p in image_paths:
                cleanup_files(p)
            cleanup_files(output_path)
            return jsonify({"error": result.message}), 400

        download_filename = request.form.get("filename", "merged.pdf")
        if not download_filename.endswith(".pdf"):
            download_filename += ".pdf"

        @after_this_request
        def _cleanup(response):
            for p in image_paths:
                cleanup_files(p)
            cleanup_files(output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=download_filename)
    except ValueError as e:
        for p in image_paths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        for p in image_paths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 500
