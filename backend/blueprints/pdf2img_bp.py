"""PDF to Images conversion routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.pdf_to_images import pdf_to_images

pdf2img_bp = Blueprint("pdf2img", __name__)


@pdf2img_bp.route("/api/pdf2img", methods=["POST"])
def pdf2img_convert():
    filepath = None
    output_dir = None
    zip_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        _fn, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        fmt = request.form.get("format", "png")
        dpi = int(request.form.get("dpi", 200))
        pages_str = request.form.get("pages", "")
        pages = [int(p.strip()) for p in pages_str.split(",") if p.strip()] if pages_str else None

        output_dir = os.path.join(Config.UPLOAD_FOLDER, f"pdf2img_{uuid.uuid4().hex[:12]}")
        result = pdf_to_images(filepath, output_dir, fmt=fmt, dpi=dpi, pages=pages)
        if not result.success:
            cleanup_files(filepath)
            return jsonify({"error": result.message}), 400

        import zipfile
        zip_name = f"{uuid.uuid4().hex}.zip"
        zip_path = os.path.join(Config.UPLOAD_FOLDER, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in result.data["files"]:
                zf.write(os.path.join(output_dir, fname), fname)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, zip_path)
            if output_dir:
                for f in os.listdir(output_dir):
                    cleanup_files(os.path.join(output_dir, f))
                try:
                    os.rmdir(output_dir)
                except OSError:
                    pass
            return response

        return send_file(zip_path, mimetype="application/zip", as_attachment=True, download_name="pdf_images.zip")
    except ValueError as e:
        cleanup_files(filepath, zip_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, zip_path)
        return jsonify({"error": str(e)}), 500
