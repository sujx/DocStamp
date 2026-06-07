"""PDF Merge routes."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.pdf_merger import merge_pdfs

pdf_merge_bp = Blueprint("pdf_merge", __name__)


@pdf_merge_bp.route("/api/pdf-merge", methods=["POST"])
def pdf_merge():
    """Merge multiple PDF files into a single PDF."""
    filepaths = []
    output_path = None
    try:
        if "files" not in request.files:
            return jsonify({"error": _("No files provided")}), 400
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            return jsonify({"error": _("No files selected")}), 400
        if len(files) < 2:
            return jsonify({"error": _("At least 2 PDF files are required")}), 400

        for f in files:
            if f.filename:
                _name, path = save_upload(f, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
                filepaths.append(path)
        if len(filepaths) < 2:
            return jsonify({"error": _("At least 2 valid PDF files are required")}), 400

        order_str = request.form.get("order", "[]")
        try:
            order = json.loads(order_str)
        except (json.JSONDecodeError, TypeError):
            order = list(range(len(filepaths)))

        sorted_paths = [filepaths[i] for i in order] if order and len(order) == len(filepaths) else filepaths

        output_name = f"{uuid.uuid4().hex}_merged.pdf"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = merge_pdfs(sorted_paths, output_path)
        if not result.success:
            for p in filepaths:
                cleanup_files(p)
            return jsonify({"error": result.message}), 400

        download_filename = request.form.get("filename", "merged.pdf")
        if not download_filename.endswith(".pdf"):
            download_filename += ".pdf"

        @after_this_request
        def _cleanup(response):
            for p in filepaths:
                cleanup_files(p)
            cleanup_files(output_path)
            return response

        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_filename,
        )
    except ValueError as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 500
