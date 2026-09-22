"""Conversion routes: /api/convert/*, /api/preview, /api/stats"""

import json
import os
import re
import uuid

from flask import Blueprint, jsonify, request
from flask_babel import gettext as _

from config import Config
from error_handler import validate_request
from schemas import MdPreviewSchema
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit

from services.converter import ConversionError, md_to_docx
from services.formatter import format_docx

convert_bp = Blueprint("convert", __name__)


# ── Helpers ─────────────────────────────────────────────────────────

STATS_FILE = os.path.join(Config.UPLOAD_FOLDER, ".stats")

ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr", "pre", "code", "blockquote",
    "em", "strong", "del", "a", "img", "ul", "ol", "li", "table", "thead", "tbody",
    "tr", "th", "td", "sup", "sub", "span", "div", "font", "b", "i", "u", "s",
    "svg", "path", "g", "defs", "use", "circle", "rect", "line", "polyline", "polygon",
    "text", "tspan", "mtext", "mrow", "mi", "mo", "mn", "msup", "msub", "mover", "munder",
    "mfrac", "msqrt", "math", "annotation", "semantics",
]
ALLOWED_ATTRS = {
    "*": ["class", "id", "style", "data-*"],
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "width", "height"],
    "svg": ["xmlns", "viewBox", "width", "height"],
    "path": ["d", "fill", "stroke", "stroke-width"],
    "circle": ["cx", "cy", "r", "fill", "stroke"],
    "rect": ["x", "y", "width", "height", "fill", "stroke"],
    "line": ["x1", "y1", "x2", "y2", "stroke"],
    "polyline": ["points", "fill", "stroke"],
    "polygon": ["points", "fill", "stroke"],
    "text": ["x", "y"],
    "math": ["xmlns", "display"],
}


def _read_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f).get("total_conversions", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def _increment_stats():
    count = _read_stats() + 1
    with open(STATS_FILE, "w") as f:
        json.dump({"total_conversions": count}, f)
    return count


def _sanitize_html(html_content):
    import bleach
    return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def _safe_download_basename(raw_name):
    raw = raw_name or "document"
    raw = re.sub(r'[\\\\/*?:"<>|]', "_", raw)
    parts = raw.replace("\\", "/").split("/")
    return parts[-1] or "document"


# ── Routes ──────────────────────────────────────────────────────────

@convert_bp.route("/api/v1/stats", methods=["GET"])
def stats():
    return jsonify({"total_conversions": _read_stats()})


@convert_bp.route("/api/v1/preview", methods=["POST"])
@validate_request(body=MdPreviewSchema)
def md_preview(body: MdPreviewSchema):
    """Render Markdown to HTML for preview."""
    import markdown
    html = markdown.markdown(body.content, extensions=[
        "tables", "fenced_code", "codehilite", "toc",
        "footnotes", "attr_list", "md_in_html",
    ])
    safe_html = _sanitize_html(html)
    return jsonify({"html": safe_html})


@convert_bp.route("/api/v1/convert", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def md_convert():
    """Convert Markdown to DOCX. Query ?format=plain skips GB/T 9704-2012 formatting."""
    filepath = None
    output_path = None
    fmt = request.args.get("format", "official")  # "official" or "plain"
    try:
        md_path = None
        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if request.content_length and request.content_length > Config.MAX_MD_SIZE:
                return jsonify({"error": _("File too large")}), 400
            _fn, filepath = save_upload(file, Config.MD_EXTENSIONS, Config.UPLOAD_FOLDER)
            md_path = filepath
        else:
            data = request.get_json(silent=True)
            if not data or "content" not in data:
                return jsonify({"error": _("No content provided")}), 400
            content = data["content"]
            if not isinstance(content, str) or not content.strip():
                return jsonify({"error": _("Content is empty")}), 400
            md_path = os.path.join(Config.UPLOAD_FOLDER, f"{uuid.uuid4().hex}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content)
            filepath = md_path

        download_id = f"{uuid.uuid4().hex}.docx"
        output_path = os.path.join(Config.UPLOAD_FOLDER, download_id)

        result = md_to_docx(md_path, output_path)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400
        title = result.data

        if fmt != "plain":
            fmt_result = format_docx(output_path)
            if not fmt_result.success:
                pass  # Best-effort formatting

        _increment_stats()

        return jsonify({
            "success": True,
            "filename": f"{_safe_download_basename(title)}.docx",
            "title": title,
            "download_id": download_id,
        })

    except (ValueError, ConversionError) as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500


@convert_bp.route("/api/v1/convert/doc2md", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
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

        filename, filepath = save_upload(file, {"docx"}, Config.UPLOAD_FOLDER)
        download_id = f"{uuid.uuid4().hex}.docx"
        output_path = os.path.join(Config.UPLOAD_FOLDER, download_id)

        import shutil
        shutil.copy2(filepath, output_path)
        fmt_result = format_docx(output_path)
        if not fmt_result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": fmt_result.message}), 400

        title = file.filename.rsplit(".", 1)[0] if file.filename else "document"

        return jsonify({
            "success": True,
            "filename": f"{_safe_download_basename(title)}.docx",
            "title": title,
            "download_id": download_id,
        })

    except (ValueError, ConversionError) as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        cleanup_files(filepath, output_path)
        return jsonify({"error": str(e)}), 500
