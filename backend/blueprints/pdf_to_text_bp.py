"""PDF to Text extraction routes."""

from flask import Blueprint, jsonify, request
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from services.pdf_to_text import extract_pdf_text, get_pdf_page_count

pdf_to_text_bp = Blueprint("pdf_to_text", __name__)


@pdf_to_text_bp.route("/api/pdf-to-text", methods=["POST"])
def pdf_to_text():
    """Extract text from a PDF file."""
    filepath = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        _fn, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)

        pages_str = request.form.get("pages", "")
        pages = None
        if pages_str:
            pages = [int(p.strip()) for p in pages_str.split(",") if p.strip()]

        total_pages_result = get_pdf_page_count(filepath)
        if not total_pages_result.success:
            return jsonify({"error": total_pages_result.message}), 400
        total_pages = total_pages_result.data

        text_result = extract_pdf_text(filepath, page_numbers=pages)
        if not text_result.success:
            return jsonify({"error": text_result.message}), 400

        return jsonify({
            "success": True,
            "text": text_result.data,
            "total_pages": total_pages,
            "extracted_pages": len(pages) if pages else total_pages,
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_files(filepath)
