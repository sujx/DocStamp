"""File operation routes: properties, watermark, PDF editor, img2pdf, print-split, excel-merge"""

import json
import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload

from services.properties import _resolve_time_props, batch_modify_properties, modify_properties, read_properties
from services.img2pdf_handler import images_to_pdf
from services.pdf_to_images import pdf_to_images
from services.print_split import split_pdf
from services.watermark import add_watermark, remove_watermark
from services.pdf_editor import pdf_delete_pages, pdf_insert_pages, pdf_reorder_pages
from services.excel_merger import StructureMismatchError, merge_excel_files

files_bp = Blueprint("files", __name__)


# ── Properties ───────────────────────────────────────────────────────

@files_bp.route("/api/properties/info", methods=["POST"])
def properties_info():
    filepath = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400
        _name, filepath = save_upload(file, Config.OFFICE_EXTENSIONS, Config.UPLOAD_FOLDER)
        props = read_properties(filepath)
        return jsonify({"success": True, "properties": props})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_files(filepath)


@files_bp.route("/api/properties", methods=["POST"])
def properties_modify():
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400
        filename, filepath = save_upload(file, Config.OFFICE_EXTENSIONS, Config.UPLOAD_FOLDER)

        props = {}
        for key in ("created", "modified", "creator", "last_modified_by", "unified_time"):
            if key in request.form and request.form[key]:
                props[key] = request.form[key]
        if not props:
            return jsonify({"error": _("No properties to modify")}), 400

        unify_time = request.form.get("unify_time", "false").lower() == "true"
        resolved = _resolve_time_props(props, unify_time)

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        modify_properties(filepath, output_path, resolved)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=filename)
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/properties/batch", methods=["POST"])
def properties_batch_modify():
    filepaths = []
    output_dir = None
    zip_path = None
    try:
        if "files" not in request.files:
            return jsonify({"error": _("No files provided")}), 400
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            return jsonify({"error": _("No files selected")}), 400

        for f in files:
            if f.filename:
                _name, path = save_upload(f, Config.OFFICE_EXTENSIONS, Config.UPLOAD_FOLDER)
                filepaths.append(path)
        if not filepaths:
            return jsonify({"error": _("No valid files uploaded")}), 400

        props = {}
        for key in ("created", "modified", "creator", "last_modified_by", "unified_time"):
            if key in request.form and request.form[key]:
                props[key] = request.form[key]
        if not props:
            return jsonify({"error": _("No properties to modify")}), 400

        unify_time = request.form.get("unify_time", "false").lower() == "true"
        output_dir = os.path.join(Config.UPLOAD_FOLDER, uuid.uuid4().hex[:12])
        os.makedirs(output_dir, exist_ok=True)
        results = batch_modify_properties(filepaths, output_dir, props, unify_time)

        import zipfile
        zip_name = f"{uuid.uuid4().hex}.zip"
        zip_path = os.path.join(Config.UPLOAD_FOLDER, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                if r["success"]:
                    zf.write(os.path.join(output_dir, r["filename"]), r["filename"])

        @after_this_request
        def _cleanup(response):
            for p in filepaths:
                cleanup_files(p)
            if output_dir:
                for f in os.listdir(output_dir):
                    cleanup_files(os.path.join(output_dir, f))
                try:
                    os.rmdir(output_dir)
                except OSError:
                    pass
            cleanup_files(zip_path)
            return response

        return send_file(zip_path, mimetype="application/zip", as_attachment=True, download_name="batch_modified.zip")
    except ValueError as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(zip_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(zip_path)
        return jsonify({"error": str(e)}), 500


# ── Image to PDF ─────────────────────────────────────────────────────

@files_bp.route("/api/img2pdf", methods=["POST"])
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
        images_to_pdf(sorted_paths, output_path, page_size)

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


# ── PDF to Images ────────────────────────────────────────────────────

@files_bp.route("/api/pdf2img", methods=["POST"])
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

        import zipfile
        zip_name = f"{uuid.uuid4().hex}.zip"
        zip_path = os.path.join(Config.UPLOAD_FOLDER, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in result["files"]:
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


# ── Print Split ──────────────────────────────────────────────────────

_tasks = {}

@files_bp.route("/api/print-split", methods=["POST"])
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
        batches = split_pdf(filepath, task_dir, batch_size)

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


@files_bp.route("/api/print-split/<task_id>/batch/<int:batch_no>", methods=["GET"])
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


# ── Watermark ────────────────────────────────────────────────────────

@files_bp.route("/api/watermark", methods=["POST"])
def watermark_add():
    filepath = None
    image_path = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.WATERMARK_EXTENSIONS, Config.UPLOAD_FOLDER)

        params_str = request.form.get("params", "{}")
        try:
            params = json.loads(params_str)
        except (json.JSONDecodeError, TypeError):
            params = {}

        watermark_type = params.get("watermark_type", "text")
        if watermark_type == "text" and not params.get("text", ""):
            return jsonify({"error": _("Watermark text is required")}), 400
        elif watermark_type == "image":
            if "watermark_image" not in request.files:
                return jsonify({"error": _("Watermark image is required")}), 400
            img_file = request.files["watermark_image"]
            if img_file.filename:
                image_name, image_path = save_upload(img_file, Config.IMAGE_EXTENSIONS, Config.UPLOAD_FOLDER)

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        add_watermark(filepath, output_path, params, image_path)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path, image_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"watermarked_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path, image_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path, image_path)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/watermark/remove", methods=["POST"])
def watermark_remove():
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.WATERMARK_EXTENSIONS, Config.UPLOAD_FOLDER)
        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = remove_watermark(filepath, output_path)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, as_attachment=True, download_name=f"cleaned_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500


# ── PDF Editor ───────────────────────────────────────────────────────

_pdf_thumbs = {}

@files_bp.route("/api/pdf-editor/info", methods=["POST"])
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
                "thumb": f"/api/pdf-editor/thumb/{os.path.basename(thumb_dir)}/{thumb_file}",
            })

        _pdf_thumbs[fn] = thumb_dir
        return jsonify({"success": True, "total_pages": total, "pages": pages_info})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/pdf-editor/thumb/<thumb_dir>/<filename>")
def pdf_editor_thumb(thumb_dir: str, filename: str):
    from werkzeug.utils import secure_filename
    safe_name = secure_filename(filename)
    safe_thumbs = secure_filename(thumb_dir)
    path = os.path.join(Config.UPLOAD_FOLDER, safe_thumbs, safe_name)
    if not os.path.isfile(path):
        return jsonify({"error": _("Thumbnail not found")}), 404
    return send_file(path, mimetype="image/png")


@files_bp.route("/api/pdf-editor/delete", methods=["POST"])
def pdf_editor_delete():
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        pages = json.loads(request.form.get("pages", "[]"))
        if not pages:
            return jsonify({"error": _("No pages specified for deletion")}), 400

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = pdf_delete_pages(filepath, output_path, pages)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=f"edited_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/pdf-editor/insert", methods=["POST"])
def pdf_editor_insert():
    filepath = None
    insert_path = None
    output_path = None
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

        at_position = int(request.form.get("at_position", 0))
        insert_pages = json.loads(request.form.get("insert_pages", "null"))

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = pdf_insert_pages(filepath, insert_path, output_path, at_position, insert_pages)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, insert_path, output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=f"merged_{filename}")
    except ValueError as e:
        cleanup_files(filepath, insert_path, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, insert_path, output_path)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/pdf-editor/reorder", methods=["POST"])
def pdf_editor_reorder():
    filepath = None
    output_path = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400

        filename, filepath = save_upload(file, Config.PDF_EXTENSIONS, Config.UPLOAD_FOLDER)
        new_order = json.loads(request.form.get("order", "[]"))
        if not new_order:
            return jsonify({"error": _("No page order specified")}), 400

        output_name = f"{uuid.uuid4().hex}_{filename}"
        output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)
        result = pdf_reorder_pages(filepath, output_path, new_order)

        @after_this_request
        def _cleanup(response):
            cleanup_files(filepath, output_path)
            return response

        return send_file(output_path, mimetype="application/pdf", as_attachment=True, download_name=f"reordered_{filename}")
    except ValueError as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500


# ── Excel Merge ──────────────────────────────────────────────────────

@files_bp.route("/api/excel-merge", methods=["POST"])
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
    except (ValueError, StructureMismatchError) as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        for p in filepaths:
            cleanup_files(p)
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 500
