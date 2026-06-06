"""Flask REST API for docStamp Document Processing Toolbox.

Provides endpoints for:
- Office document property modification (.docx/.xlsx/.pptx)
- Markdown to GB/T 9704-2012 DOCX conversion
- DOCX format normalization
- Image to PDF merging (PNG/JPEG/TIFF)
- PDF print batch splitting
- Word/PDF watermark management
- Async task tracking (SSE + polling)
"""

import json
import logging
import os
import re
import sys
import uuid
import time

from flask import (
    Flask, Response, request, jsonify, send_file, send_from_directory,
    after_this_request, g,
)
from flask_babel import Babel, gettext as _
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from json_logging import setup_json_logging
from error_handler import register_error_handlers, validate_request
from cache import init_cache
from models import init_db, TaskRecord, OperationLog
from schemas import (
    MdConvertSchema, MdPreviewSchema,
    PropertiesModifySchema,
    Img2PdfSchema, Pdf2ImgSchema,
    PrintSplitSchema,
    WatermarkAddSchema,
    PdfDeleteSchema, PdfInsertSchema, PdfReorderSchema,
    ExcelMergeSchema,
)

from properties import modify_properties, read_properties, batch_modify_properties
from img2pdf_handler import images_to_pdf
from print_split import split_pdf
from watermark import add_watermark, remove_watermark
from pdf_editor import pdf_delete_pages, pdf_insert_pages, pdf_reorder_pages
from excel_merger import merge_excel_files, StructureMismatchError
from pdf_to_images import pdf_to_images
from converter import md_to_docx, ConversionError
from formatter import format_docx


# ── Logging ───────────────────────────────────────────────────────────

def _setup_logging(app: Flask) -> None:
    """Configure JSON-structured logging with daily rotation (30-day retention)."""
    setup_json_logging(app)


# ── Application Factory ─────────────────────────────────────────────────

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="",
    )
    app.config.from_object(Config)

    # i18n
    def get_locale():
        return request.accept_languages.best_match(
            app.config.get("LANGUAGES", ["en", "zh_CN"]), default="en"
        )

    Babel(app, default_locale="en", locale_selector=get_locale)
    CORS(app)

    # Infrastructure (order matters: logging → error handlers → cache → DB)
    _setup_logging(app)
    register_error_handlers(app)
    init_cache(app)
    init_db(app.config["TASK_DB_PATH"])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    _register_routes(app)

    app.logger.info("docStamp application initialized")
    return app


def _register_routes(app: Flask) -> None:
    """Register all API routes on the Flask app."""

    # ── Helpers ────────────────────────────────────────────────────

    def _validate_filename(raw_name: str, allowed_exts: set) -> str:
        """Validate and sanitize a filename."""
        if not raw_name:
            raise ValueError(_("No filename provided"))
        for char in app.config["FORBIDDEN_PATH_CHARS"]:
            if char in raw_name:
                raise ValueError(_("Invalid characters in filename"))
        ext = raw_name.rsplit(".", 1)[-1].lower() if "." in raw_name else ""
        if ext not in allowed_exts:
            raise ValueError(
                _("File extension .%(ext)s is not allowed") % {"ext": ext}
            )
        filename = secure_filename(raw_name)
        if not filename:
            raise ValueError(_("Invalid filename after sanitization"))
        if not filename.lower().endswith(f".{ext}"):
            filename = f"{filename}.{ext}"
        return filename

    def _save_upload(file, allowed_exts: set) -> tuple:
        """Save an uploaded file. Returns (filename, filepath)."""
        filename = _validate_filename(file.filename, allowed_exts)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)
        app.logger.info("File saved: %s", unique_name)
        return unique_name, filepath

    def _cleanup_files(*paths: str) -> None:
        """Remove files from disk, ignoring errors."""
        for path in paths:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

    # ── Static file serving (production) ──────────────────────────

    static_dir = app.config["STATIC_FOLDER"]

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        """Serve the Vue.js frontend SPA."""
        if not os.path.isdir(static_dir):
            return jsonify({
                "error": _(
                    "Frontend not built. Run 'npm run build' in frontend/ "
                    "or set DOCSTAMP_STATIC env var."
                )
            }), 503
        if path and os.path.isfile(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        index_path = os.path.join(static_dir, "index.html")
        if os.path.isfile(index_path):
            return send_from_directory(static_dir, "index.html")
        return jsonify({"error": _("Frontend index.html not found")}), 503

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    # ── Feature 1: Properties ──────────────────────────────────────

    @app.route("/api/properties/info", methods=["POST"])
    def properties_info():
        """Read current properties of an Office document."""
        filepath = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            _name, filepath = _save_upload(file, app.config["OFFICE_EXTENSIONS"])
            props = read_properties(filepath)
            return jsonify({"success": True, "properties": props})

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error reading properties")
            return jsonify({"error": str(e)}), 500
        finally:
            _cleanup_files(filepath)

    @app.route("/api/properties", methods=["POST"])
    def properties_modify():
        """Modify Office document properties and return the file."""
        filepath = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["OFFICE_EXTENSIONS"]
            )

            # Parse properties from form data
            props = {}
            for key in ("created", "modified", "creator", "last_modified_by",
                        "unified_time"):
                if key in request.form and request.form[key]:
                    props[key] = request.form[key]

            if not props:
                return jsonify({"error": _("No properties to modify")}), 400

            # Support unify_time mode
            unify_time = request.form.get("unify_time", "false").lower() == "true"

            # Resolve time properties
            from properties import _resolve_time_props
            resolved_props = _resolve_time_props(props, unify_time)

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            modify_properties(filepath, output_path, resolved_props)
            app.logger.info("Properties modified: %s", filename)

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, output_path)
                return response

            return send_file(
                output_path,
                as_attachment=True,
                download_name=filename,
            )

        except ValueError as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error modifying properties")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/properties/batch", methods=["POST"])
    def properties_batch_modify():
        """Batch modify properties for multiple Office documents.

        Accepts multiple files and applies the same properties to all.
        Supports:
        - `unify_time=true`: set both created and modified to the same value
        - `unified_time`: a single time value for both fields
        - Returns a ZIP file containing all modified documents.
        """
        filepaths = []
        output_dir = None
        zip_path = None
        try:
            if "files" not in request.files:
                return jsonify({"error": _("No files provided")}), 400

            files = request.files.getlist("files")
            if not files or all(not f.filename for f in files):
                return jsonify({"error": _("No files selected")}), 400

            # Save all files
            for f in files:
                if f.filename:
                    _name, path = _save_upload(f, app.config["OFFICE_EXTENSIONS"])
                    filepaths.append(path)

            if not filepaths:
                return jsonify({"error": _("No valid files uploaded")}), 400

            # Parse properties from form data
            props = {}
            for key in ("created", "modified", "creator", "last_modified_by",
                        "unified_time"):
                if key in request.form and request.form[key]:
                    props[key] = request.form[key]

            if not props:
                return jsonify({"error": _("No properties to modify")}), 400

            unify_time = request.form.get("unify_time", "false").lower() == "true"

            # Create output directory for batch results
            output_dir = os.path.join(
                app.config["UPLOAD_FOLDER"], uuid.uuid4().hex[:12]
            )
            os.makedirs(output_dir, exist_ok=True)

            results = batch_modify_properties(
                filepaths, output_dir, props, unify_time
            )

            # Create ZIP of all results
            import zipfile
            zip_name = f"{uuid.uuid4().hex}.zip"
            zip_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_name)

            success_count = 0
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in results:
                    if r["success"]:
                        zf.write(
                            os.path.join(output_dir, r["filename"]),
                            r["filename"],
                        )
                        success_count += 1

            app.logger.info(
                "Batch properties: %d/%d files modified",
                success_count, len(results)
            )

            @after_this_request
            def _cleanup_response(response):
                for p in filepaths:
                    _cleanup_files(p)
                if output_dir:
                    for f in os.listdir(output_dir):
                        _cleanup_files(os.path.join(output_dir, f))
                    try:
                        os.rmdir(output_dir)
                    except OSError:
                        pass
                _cleanup_files(zip_path)
                return response

            return send_file(
                zip_path,
                mimetype="application/zip",
                as_attachment=True,
                download_name="batch_modified.zip",
            )

        except ValueError as e:
            for p in filepaths:
                _cleanup_files(p)
            _cleanup_files(zip_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error in batch properties modification")
            for p in filepaths:
                _cleanup_files(p)
            _cleanup_files(zip_path)
            return jsonify({"error": str(e)}), 500

    # ── Feature 2: Image to PDF ────────────────────────────────────

    @app.route("/api/img2pdf", methods=["POST"])
    def img2pdf_merge():
        """Merge images into a single PDF."""
        image_paths = []
        output_path = None
        try:
            if "files" not in request.files:
                return jsonify({"error": _("No files provided")}), 400

            files = request.files.getlist("files")
            if not files or all(not f.filename for f in files):
                return jsonify({"error": _("No files selected")}), 400

            # Save all images
            for f in files:
                if f.filename:
                    _name, path = _save_upload(f, app.config["IMAGE_EXTENSIONS"])
                    image_paths.append(path)

            if not image_paths:
                return jsonify({"error": _("No valid images uploaded")}), 400

            # Parse order array from form data
            order_str = request.form.get("order", "[]")
            try:
                order = json.loads(order_str)
            except (json.JSONDecodeError, TypeError):
                order = list(range(len(image_paths)))

            # Reorder images according to sort array
            if order and len(order) == len(image_paths):
                sorted_paths = [image_paths[i] for i in order]
            else:
                sorted_paths = image_paths

            # Page size option
            page_size = request.form.get("page_size", "original")

            output_name = f"{uuid.uuid4().hex}.pdf"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            images_to_pdf(sorted_paths, output_path, page_size)
            app.logger.info(
                "Merged %d images into PDF: %s", len(sorted_paths), output_name
            )

            # Custom filename from frontend
            download_filename = request.form.get("filename", "merged.pdf")
            if not download_filename.endswith(".pdf"):
                download_filename += ".pdf"

            @after_this_request
            def _cleanup_response(response):
                for p in image_paths:
                    _cleanup_files(p)
                _cleanup_files(output_path)
                return response

            return send_file(
                output_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=download_filename,
            )

        except ValueError as e:
            for p in image_paths:
                _cleanup_files(p)
            _cleanup_files(output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error merging images to PDF")
            for p in image_paths:
                _cleanup_files(p)
            _cleanup_files(output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pdf2img", methods=["POST"])
    def pdf2img_convert():
        """Convert PDF pages to images, returned as a ZIP file."""
        filepath = None
        output_dir = None
        zip_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            _fn, filepath = _save_upload(file, app.config["PDF_EXTENSIONS"])

            fmt = request.form.get("format", "png")
            dpi = int(request.form.get("dpi", 200))
            pages_str = request.form.get("pages", "")
            pages = None
            if pages_str:
                pages = [int(p.strip()) for p in pages_str.split(",") if p.strip()]

            output_dir = os.path.join(
                app.config["UPLOAD_FOLDER"], f"pdf2img_{uuid.uuid4().hex[:12]}"
            )
            result = pdf_to_images(filepath, output_dir, fmt=fmt, dpi=dpi, pages=pages)

            # Create ZIP of all images
            import zipfile
            zip_name = f"{uuid.uuid4().hex}.zip"
            zip_path = os.path.join(app.config["UPLOAD_FOLDER"], zip_name)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in result["files"]:
                    zf.write(os.path.join(output_dir, fname), fname)

            app.logger.info(
                "Converted %d PDF pages to %s images at %d DPI",
                result["converted"], fmt, dpi
            )

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, zip_path)
                if output_dir:
                    for f in os.listdir(output_dir):
                        _cleanup_files(os.path.join(output_dir, f))
                    try:
                        os.rmdir(output_dir)
                    except OSError:
                        pass
                return response

            return send_file(
                zip_path,
                mimetype="application/zip",
                as_attachment=True,
                download_name="pdf_images.zip",
            )

        except ValueError as e:
            _cleanup_files(filepath, zip_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error converting PDF to images")
            _cleanup_files(filepath, zip_path)
            return jsonify({"error": str(e)}), 500

    # ── Feature 3: Print Split ─────────────────────────────────────

    # In-memory task store (for demo/single-instance use)
    _tasks = {}

    @app.route("/api/print-split", methods=["POST"])
    def print_split_create():
        """Split a PDF into print batches."""
        filepath = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["PDF_EXTENSIONS"]
            )

            batch_size = int(request.form.get("batch_size", 60))
            interval_seconds = int(request.form.get("interval", 60))

            if batch_size < 1:
                return jsonify({"error": _("Batch size must be at least 1")}), 400
            if interval_seconds < 0:
                return jsonify({"error": _("Interval must be non-negative")}), 400

            task_id = uuid.uuid4().hex[:12]
            task_dir = os.path.join(app.config["UPLOAD_FOLDER"], task_id)
            os.makedirs(task_dir, exist_ok=True)

            batches = split_pdf(filepath, task_dir, batch_size)

            _tasks[task_id] = {
                "task_dir": task_dir,
                "batches": batches,
                "filepath": filepath,
            }

            app.logger.info(
                "PDF split into %d batches (task: %s)", len(batches), task_id
            )

            return jsonify({
                "success": True,
                "task_id": task_id,
                "total_pages": sum(b["pages"] for b in batches),
                "batch_count": len(batches),
                "batches": batches,
            })

        except ValueError as e:
            _cleanup_files(filepath)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error splitting PDF")
            _cleanup_files(filepath)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/print-split/<task_id>/batch/<int:batch_no>", methods=["GET"])
    def print_split_download(task_id: str, batch_no: int):
        """Download a specific batch of a print-split task."""
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

            app.logger.info(
                "Downloading batch %d/%d for task %s",
                batch_no, len(batches), task_id
            )

            return send_file(
                batch_file,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=batch["filename"],
            )

        except Exception as e:
            app.logger.exception("Error downloading batch")
            return jsonify({"error": str(e)}), 500

    # ── Feature 4: Watermark ───────────────────────────────────────

    @app.route("/api/watermark", methods=["POST"])
    def watermark_add():
        """Add watermark to a Word or PDF file.

        Supports text and image watermarks.
        """
        filepath = None
        image_path = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["WATERMARK_EXTENSIONS"]
            )

            # Parse watermark parameters
            params_str = request.form.get("params", "{}")
            try:
                params = json.loads(params_str)
            except (json.JSONDecodeError, TypeError):
                params = {}

            watermark_type = params.get("watermark_type", "text")

            # Validate required params based on type
            if watermark_type == "text":
                if not params.get("text", ""):
                    return jsonify({"error": _("Watermark text is required")}), 400
            elif watermark_type == "image":
                if "watermark_image" not in request.files:
                    return jsonify({"error": _("Watermark image is required")}), 400
                img_file = request.files["watermark_image"]
                if img_file.filename:
                    image_name, image_path = _save_upload(
                        img_file, app.config["IMAGE_EXTENSIONS"]
                    )

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            add_watermark(filepath, output_path, params, image_path)
            app.logger.info("Watermark added to: %s", filename)

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, output_path, image_path)
                return response

            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"watermarked_{filename}",
            )

        except ValueError as e:
            _cleanup_files(filepath, output_path, image_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error adding watermark")
            _cleanup_files(filepath, output_path, image_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/watermark/remove", methods=["POST"])
    def watermark_remove():
        """Remove watermarks from a Word or PDF file."""
        filepath = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["WATERMARK_EXTENSIONS"]
            )

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            result = remove_watermark(filepath, output_path)
            app.logger.info("Watermark removed from: %s (%s)", filename, result["method"])

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, output_path)
                return response

            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"cleaned_{filename}",
            )

        except ValueError as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error removing watermark")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    # ── Feature 5: PDF Editor (delete/insert/reorder) ────────────────
    @app.route("/api/pdf-editor/info", methods=["POST"])
    def pdf_editor_info():
        """Get page count and generate preview thumbnails for a PDF."""
        filepath = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            fn, filepath = _save_upload(
                file, app.config["PDF_EXTENSIONS"]
            )

            from pypdf import PdfReader

            reader = PdfReader(filepath)
            total = len(reader.pages)
            max_preview = min(total, 50)

            # Generate thumbnails using pdftoppm
            thumb_dir = os.path.join(
                app.config["UPLOAD_FOLDER"], f"thumbs_{uuid.uuid4().hex[:8]}"
            )
            os.makedirs(thumb_dir, exist_ok=True)

            import subprocess
            thumb_prefix = os.path.join(thumb_dir, "page")
            try:
                subprocess.run(
                    [
                        "pdftoppm", "-png", "-scale-to", "200",
                        "-f", "1", "-l", str(max_preview),
                        filepath, thumb_prefix,
                    ],
                    check=True, capture_output=True, timeout=30,
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                app.logger.warning("pdftoppm failed: %s, falling back", e)
                # Fallback: create blank placeholder thumbs with Pillow
                from PIL import Image as PILImage, ImageDraw
                for i in range(max_preview):
                    page = reader.pages[i]
                    w = max(int(float(page.mediabox.width) * 0.25), 80)
                    h = max(int(float(page.mediabox.height) * 0.25), 100)
                    img = PILImage.new("RGB", (w, h), "white")
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([0, 0, w-1, h-1], outline="#d9d6c5")
                    draw.text((w//2-25, h//2-6), f"Page {i+1}", fill="#8c8a7a")
                    img.save(os.path.join(thumb_dir, f"page-{i+1}.png"), "PNG")

            # Build pages info with thumbnail paths
            # pdftoppm outputs: page-1.png, page-2.png, ... (no leading zeros)
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

            # Store thumb_dir for cleanup (associate with filepath)
            _pdf_thumbs[fn] = thumb_dir

            return jsonify({
                "success": True,
                "total_pages": total,
                "pages": pages_info,
            })

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error getting PDF info")
            return jsonify({"error": str(e)}), 500

    # Thumbnail cache: filename → thumb_dir
    _pdf_thumbs = {}

    @app.route("/api/pdf-editor/thumb/<thumb_dir>/<filename>")
    def pdf_editor_thumb(thumb_dir: str, filename: str):
        """Serve a generated page thumbnail image."""
        safe_name = secure_filename(filename)
        safe_thumbs = secure_filename(thumb_dir)
        base = app.config["UPLOAD_FOLDER"]
        path = os.path.join(base, safe_thumbs, safe_name)
        if not os.path.isfile(path):
            return jsonify({"error": _("Thumbnail not found")}), 404
        return send_file(path, mimetype="image/png")

    @app.route("/api/pdf-editor/delete", methods=["POST"])
    def pdf_editor_delete():
        """Delete specified pages from a PDF."""
        filepath = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["PDF_EXTENSIONS"]
            )

            pages = json.loads(request.form.get("pages", "[]"))
            if not pages:
                return jsonify({"error": _("No pages specified for deletion")}), 400

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            result = pdf_delete_pages(filepath, output_path, pages)
            app.logger.info(
                "Deleted %d pages from %s (kept %d)",
                result["deleted_pages"], filename, result["remaining_pages"]
            )

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, output_path)
                return response

            return send_file(
                output_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"edited_{filename}",
            )

        except ValueError as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error deleting PDF pages")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pdf-editor/insert", methods=["POST"])
    def pdf_editor_insert():
        """Insert pages from another PDF into the source PDF."""
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

            filename, filepath = _save_upload(
                file, app.config["PDF_EXTENSIONS"]
            )
            _name2, insert_path = _save_upload(
                insert_file, app.config["PDF_EXTENSIONS"]
            )

            at_position = int(request.form.get("at_position", 0))
            insert_pages = json.loads(request.form.get("insert_pages", "null"))

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            result = pdf_insert_pages(
                filepath, insert_path, output_path, at_position, insert_pages
            )
            app.logger.info(
                "Inserted %d pages into %s (final: %d pages)",
                result["inserted_pages"], filename, result["final_pages"]
            )

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, insert_path, output_path)
                return response

            return send_file(
                output_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"merged_{filename}",
            )

        except ValueError as e:
            _cleanup_files(filepath, insert_path, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error inserting PDF pages")
            _cleanup_files(filepath, insert_path, output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pdf-editor/reorder", methods=["POST"])
    def pdf_editor_reorder():
        """Reorder pages of a PDF."""
        filepath = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(
                file, app.config["PDF_EXTENSIONS"]
            )

            new_order = json.loads(request.form.get("order", "[]"))
            if not new_order:
                return jsonify({"error": _("No page order specified")}), 400

            output_name = f"{uuid.uuid4().hex}_{filename}"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            result = pdf_reorder_pages(filepath, output_path, new_order)
            app.logger.info(
                "Reordered %d pages in %s", result["total_pages"], filename
            )

            @after_this_request
            def _cleanup_response(response):
                _cleanup_files(filepath, output_path)
                return response

            return send_file(
                output_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"reordered_{filename}",
            )

        except ValueError as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error reordering PDF pages")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    # ── Feature 6: Excel Merge ───────────────────────────────────────

    @app.route("/api/excel-merge", methods=["POST"])
    def excel_merge():
        """Merge multiple .xlsx files with the same structure into one."""
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

            # Save all files
            filenames = []
            for f in files:
                if f.filename:
                    _fn, path = _save_upload(f, app.config["EXCEL_EXTENSIONS"])
                    filepaths.append(path)
                    filenames.append(_fn)

            if len(filepaths) < 2:
                return jsonify({"error": _("At least 2 valid Excel files are required")}), 400

            output_name = f"{uuid.uuid4().hex}_merged.xlsx"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)

            result = merge_excel_files(filepaths, output_path)
            app.logger.info(
                "Merged %d Excel files: %d total rows", result["file_count"], result["total_rows"]
            )

            download_filename = request.form.get("filename", "merged.xlsx")
            if not download_filename.endswith(".xlsx"):
                download_filename += ".xlsx"

            @after_this_request
            def _cleanup_response(response):
                for p in filepaths:
                    _cleanup_files(p)
                _cleanup_files(output_path)
                return response

            return send_file(
                output_path,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=download_filename,
            )

        except (ValueError, StructureMismatchError) as e:
            for p in filepaths:
                _cleanup_files(p)
            _cleanup_files(output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error merging Excel files")
            for p in filepaths:
                _cleanup_files(p)
            _cleanup_files(output_path)
            return jsonify({"error": str(e)}), 500

    # ── Feature 7: MD to DOCX (GB/T 9704-2012) ──────────────────────

    # Stats helpers
    STATS_FILE = os.path.join(app.config["UPLOAD_FOLDER"], ".stats")

    def _read_stats():
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
                return data.get("total_conversions", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def _increment_stats():
        count = _read_stats() + 1
        with open(STATS_FILE, "w") as f:
            json.dump({"total_conversions": count}, f)
        return count

    # HTML sanitizer (bleach)
    ALLOWED_TAGS = [
        "h1","h2","h3","h4","h5","h6","p","br","hr","pre","code","blockquote",
        "em","strong","del","a","img","ul","ol","li","table","thead","tbody",
        "tr","th","td","sup","sub","span","div","font","b","i","u","s",
        "svg","path","g","defs","use","circle","rect","line","polyline","polygon",
        "text","tspan","mtext","mrow","mi","mo","mn","msup","msub","mover","munder",
        "mfrac","msqrt","math","annotation","semantics",
    ]
    ALLOWED_ATTRS = {
        "*": ["class","id","style","data-*"],
        "a": ["href","title","target"],
        "img": ["src","alt","width","height"],
        "svg": ["xmlns","viewBox","width","height"],
        "path": ["d","fill","stroke","stroke-width"],
        "circle": ["cx","cy","r","fill","stroke"],
        "rect": ["x","y","width","height","fill","stroke"],
        "line": ["x1","y1","x2","y2","stroke"],
        "polyline": ["points","fill","stroke"],
        "polygon": ["points","fill","stroke"],
        "text": ["x","y"],
        "math": ["xmlns","display"],
    }

    def _sanitize_html(html_content):
        import bleach
        return bleach.clean(
            html_content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )

    def _safe_download_basename(raw_name):
        """Extract download-safe basename preserving non-ASCII chars."""
        raw = raw_name or "document"
        raw = re.sub(r'[\\\\/*?:"<>|]', "_", raw)
        parts = raw.replace("\\", "/").split("/")
        return parts[-1] or "document"

    @app.route("/api/stats", methods=["GET"])
    def stats():
        return jsonify({"total_conversions": _read_stats()})

    @app.route("/api/preview", methods=["POST"])
    def md_preview():
        """Render Markdown to HTML for preview."""
        try:
            data = request.get_json(silent=True)
            if not data or "content" not in data:
                return jsonify({"error": _("No content provided")}), 400
            content = data["content"]
            if not isinstance(content, str):
                return jsonify({"error": _("Content must be a string")}), 400

            import markdown
            html = markdown.markdown(content, extensions=[
                "tables", "fenced_code", "codehilite", "toc",
                "footnotes", "attr_list", "md_in_html",
            ])
            safe_html = _sanitize_html(html)
            return jsonify({"html": safe_html})
        except Exception as e:
            app.logger.exception("Error rendering preview")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/convert", methods=["POST"])
    def md_convert():
        """Convert Markdown to GB/T 9704-2012 DOCX."""
        filepath = None
        output_path = None
        try:
            md_path = None
            if "file" in request.files and request.files["file"].filename:
                file = request.files["file"]
                if request.content_length and request.content_length > app.config["MAX_MD_SIZE"]:
                    return jsonify({"error": _("File too large")}), 400
                _fn, filepath = _save_upload(file, app.config["MD_EXTENSIONS"])
                md_path = filepath
            else:
                data = request.get_json(silent=True)
                if not data or "content" not in data:
                    return jsonify({"error": _("No content provided")}), 400
                content = data["content"]
                if not isinstance(content, str) or not content.strip():
                    return jsonify({"error": _("Content is empty")}), 400
                md_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{uuid.uuid4().hex}.md")
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(content)
                filepath = md_path

            download_id = f"{uuid.uuid4().hex}.docx"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], download_id)

            title = md_to_docx(md_path, output_path)

            try:
                format_docx(output_path)
            except Exception as e:
                app.logger.warning("DOCX formatting failed, using unformatted: %s", e)

            _increment_stats()

            return jsonify({
                "success": True,
                "filename": f"{_safe_download_basename(title)}.docx",
                "title": title,
                "download_id": download_id,
            })

        except (ValueError, ConversionError) as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error converting MD to DOCX")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/convert/doc2md", methods=["POST"])
    def format_docx_endpoint():
        """Reformat an existing DOCX per GB/T 9704-2012."""
        filepath = None
        output_path = None
        try:
            if "file" not in request.files:
                return jsonify({"error": _("No file provided")}), 400
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": _("No file selected")}), 400

            filename, filepath = _save_upload(file, {"docx"})
            download_id = f"{uuid.uuid4().hex}.docx"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], download_id)

            import shutil
            shutil.copy2(filepath, output_path)
            format_docx(output_path)

            # Use original filename (before UUID prefix) as output title
            title = file.filename.rsplit(".", 1)[0] if file.filename else "document"

            return jsonify({
                "success": True,
                "filename": f"{_safe_download_basename(title)}.docx",
                "title": title,
                "download_id": download_id,
            })

        except (ValueError, ConversionError) as e:
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.exception("Error formatting DOCX")
            _cleanup_files(filepath, output_path)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/download/<filename>")
    def download_file(filename: str):
        """Serve a generated file for download with Range request support.

        Supports:
        - Full download (200 OK)
        - Partial download (206 Partial Content) via Range header
        """
        for char in app.config["FORBIDDEN_PATH_CHARS"]:
            if char in filename:
                return jsonify({"error": _("Invalid filename")}), 400
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in app.config["DOWNLOAD_EXTENSIONS"]:
            return jsonify({"error": _("File type not allowed for download")}), 400
        safe_name = secure_filename(filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        if not os.path.isfile(filepath):
            return jsonify({"error": _("File not found")}), 404

        file_size = os.path.getsize(filepath)
        range_header = request.headers.get("Range")

        mimetype = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if ext == "docx" else "text/markdown"
        )

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
            response = send_file(
                filepath, mimetype=mimetype, as_attachment=True,
                download_name=safe_name,
            )
            response.headers["Accept-Ranges"] = "bytes"
            response.headers["Content-Length"] = str(file_size)
        return response

    # ── Async Task Endpoints ──────────────────────────────────────────

    # Shared model instances
    _task_record = TaskRecord(app.config["TASK_DB_PATH"])
    _op_log = OperationLog(app.config["TASK_DB_PATH"])

    def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
        """Parse HTTP Range header into (start_byte, end_byte)."""
        try:
            unit, ranges = range_header.split("=")
            if unit != "bytes":
                raise ValueError("Only bytes range is supported")
            start_str, end_str = ranges.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            return start, end
        except (ValueError, AttributeError):
            return 0, file_size - 1

    def _read_file_chunk(filepath: str, start: int, end: int) -> bytes:
        """Read a byte range from a file."""
        with open(filepath, "rb") as f:
            f.seek(start)
            return f.read(end - start + 1)

    @app.route("/api/tasks/<task_id>")
    def task_status(task_id: str):
        """Poll endpoint: return current task status."""
        record = _task_record.get_by_id(task_id)
        if not record:
            return jsonify({
                "code": 404,
                "msg": "任务未找到",
                "requestId": getattr(g, "request_id", "-"),
            }), 404
        return jsonify({
            "code": 200,
            "data": record,
            "requestId": getattr(g, "request_id", "-"),
        })

    @app.route("/api/tasks/<task_id>/stream")
    def task_stream(task_id: str):
        """SSE endpoint: real-time task progress push."""

        def generate():
            record = _task_record.get_by_id(task_id)
            if not record:
                yield f"event: error\ndata: {json.dumps({'error': 'TASK_NOT_FOUND'})}\n\n"
                return

            last_updated = None
            while True:
                record = _task_record.get_by_id(task_id)
                if record is None:
                    break
                if record["updated_at"] != last_updated:
                    last_updated = record["updated_at"]
                    payload = {k: record[k] for k in record.keys()}
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                if record["status"] in ("success", "failure"):
                    return
                time.sleep(1)

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )


# ── Entry point ──────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
