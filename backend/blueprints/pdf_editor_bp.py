"""PDF page editor routes: delete, insert, reorder, thumbnails."""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.pdf_editor import pdf_delete_pages, pdf_insert_pages, pdf_reorder_pages

pdf_editor_bp = Blueprint("pdf_editor", __name__)


def _pdf_edit_route(service_fn, parse_form, download_prefix):
    """Shared handler for single-file PDF edit routes (upload → process → cleanup → send).

    Args:
        service_fn: callable(filepath, output_path, **form_data) → ServiceResult
        parse_form: callable(request) → dict of form parameters (may raise ValueError)
        download_prefix: prefix for download filename (e.g. "edited", "reordered")
    """
    cleanup_paths = []
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        cleanup_paths.append(filepath)

        form_data = parse_form(request)

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        cleanup_paths.append(output_path)

        result = service_fn(filepath, output_path, **form_data)
        if not result.success:
            cleanup_files(*cleanup_paths)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(*cleanup_paths)
            return response

        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{download_prefix}_{filename}",
        )
    except ValueError as e:
        cleanup_files(*cleanup_paths)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(*cleanup_paths)
        return jsonify({"error": str(e)}), 500


@pdf_editor_bp.route("/api/v1/pdf-editor/info", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def pdf_editor_info():
    filepath = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        fn, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)

        from pypdf import PdfReader
        reader = PdfReader(filepath)
        total = len(reader.pages)
        max_preview = min(total, 50)

        thumb_dir = os.path.join(Config.UPLOAD_FOLDER, f"thumbs_{uuid.uuid4().hex[:8]}")
        os.makedirs(thumb_dir, exist_ok=True)

        import subprocess
        thumb_prefix = os.path.join(thumb_dir, "page")
        try:
            subprocess.run(
                ["pdftoppm", "-png", "-scale-to", "200", "-f", "1", "-l", str(max_preview),
                 filepath, thumb_prefix],
                check=True, capture_output=True, timeout=30,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            from PIL import Image as PILImage, ImageDraw
            for i in range(max_preview):
                page = reader.pages[i]
                w = max(int(float(page.mediabox.width) * 0.25), 80)
                h = max(int(float(page.mediabox.height) * 0.25), 100)
                img = PILImage.new("RGB", (w, h), "white")
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, w - 1, h - 1], outline="#d9d6c5")
                draw.text((w // 2 - 25, h // 2 - 6), f"Page {i+1}", fill="#8c8a7a")
                img.save(os.path.join(thumb_dir, f"page-{i+1}.png"), "PNG")

        pages_info = []
        for i in range(max_preview):
            thumb_file = f"page-{i+1}.png"
            page = reader.pages[i]
            pages_info.append({
                "page_no": i + 1,
                "width": float(page.mediabox.width),
                "height": float(page.mediabox.height),
                "thumb": f"/api/v1/pdf-editor/thumb/{os.path.basename(thumb_dir)}/{thumb_file}",
            })

        return jsonify({"success": True, "total_pages": total, "pages": pages_info})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_files(filepath)


@pdf_editor_bp.route("/api/v1/pdf-editor/thumb/<thumb_dir>/<filename>")
def pdf_editor_thumb(thumb_dir: str, filename: str):
    safe_name = secure_filename(filename)
    safe_thumbs = secure_filename(thumb_dir)
    path = os.path.join(Config.UPLOAD_FOLDER, safe_thumbs, safe_name)
    if not os.path.isfile(path):
        return jsonify({"error": _("Thumbnail not found")}), 404
    return send_file(path, mimetype="image/png")


@pdf_editor_bp.route("/api/v1/pdf-editor/delete", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def pdf_editor_delete():
    def parse_form(req):
        pages = json.loads(req.form.get("pages", "[]"))
        if not pages:
            raise ValueError(_("No pages specified for deletion"))
        return {"pages": pages}

    return _pdf_edit_route(pdf_delete_pages, parse_form, "edited")


@pdf_editor_bp.route("/api/v1/pdf-editor/insert", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def pdf_editor_insert():
    cleanup_paths = []
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No source file provided")}), 400
        if "insert_file" not in request.files:
            return jsonify({"error": _("No insert file provided")}), 400

        file = request.files["file"]
        insert_file = request.files["insert_file"]
        if not file.filename or not insert_file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        _name2, insert_path = save_upload(insert_file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        cleanup_paths.extend([filepath, insert_path])

        at_position = int(request.form.get("at_position", 0))
        insert_pages = json.loads(request.form.get("insert_pages", "null"))

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        cleanup_paths.append(output_path)

        result = pdf_insert_pages(filepath, insert_path, output_path, at_position, insert_pages)
        if not result.success:
            cleanup_files(*cleanup_paths)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(*cleanup_paths)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=f"merged_{filename}")
    except ValueError as e:
        cleanup_files(*cleanup_paths)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(*cleanup_paths)
        return jsonify({"error": str(e)}), 500


@pdf_editor_bp.route("/api/v1/pdf-editor/reorder", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def pdf_editor_reorder():
    def parse_form(req):
        new_order = json.loads(req.form.get("order", "[]"))
        if not new_order:
            raise ValueError(_("No page order specified"))
        return {"new_order": new_order}

    return _pdf_edit_route(pdf_reorder_pages, parse_form, "reordered")
