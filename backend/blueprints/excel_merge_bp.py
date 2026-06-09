"""Excel/CSV merge routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.excel_merger import merge_excel_files

excel_merge_bp = Blueprint("excel_merge", __name__)


@excel_merge_bp.route("/api/v1/excel-merge", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def excel_merge():
    filepaths = []
    output_path = None
    try:
        if "files" not in request.files:
            return jsonify({"error": _("No files provided")}), 400
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            return jsonify({"error": _("No files selected")}), 400
        if len(files) < 2:
            return jsonify({"error": _("At least 2 files are required for merging")}), 400

        for f in files:
            if f.filename:
                _fn, path = save_upload(f, Config.EXCEL_EXTENSIONS, Config.UPLOAD_FOLDER)
                filepaths.append(path)
        if len(filepaths) < 2:
            return jsonify({"error": _("At least 2 valid Excel files are required")}), 400

        output_name = f"{uuid.uuid4().hex}_merged.xlsx"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = merge_excel_files(filepaths, output_path)
        if not result.success:
            for p in filepaths:
                cleanup_files(p)
            cleanup_files(output_path)
            return jsonify({"error": result.message}), 400

        download_filename = request.form.get("filename", "merged.xlsx")
        if not download_filename.endswith(".xlsx"):
            download_filename += ".xlsx"

        @after_this_request
        def _cleanup(response):
            for p in filepaths:
                cleanup_files(p)
            cleanup_files(output_path)
            return response

        return send_file(
            output_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
