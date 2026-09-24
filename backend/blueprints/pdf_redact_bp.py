"""PDF redaction routes: session upload, page preview, search, apply, download.

A session is one uploaded PDF living in its own directory under the upload
folder, addressed by an unguessable 32-hex id. That id is the whole capability:
the page, search, apply and download routes all resolve it from disk, so a
worker that never saw the upload can still serve the follow-up request, and one
session can only ever read its own files.
"""

import io
import os

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils import redact_session
from utils.base.file_helpers import safe_download_name, validate_filename
from utils.file_security import validate_file_security
from utils.rate_limit import rate_limit
from services.pdf_redact import (
    DEFAULT_MOSAIC_BLOCK,
    MAX_PAGES,
    find_text_matches,
    inspect_pdf,
    redact_pdf,
)

pdf_redact_bp = Blueprint("pdf_redact", __name__)

#: Preview DPI is a bandwidth/legibility trade-off, not a quality setting: the
#: page image only has to be good enough to draw boxes on.
DEFAULT_DPI = 110
MIN_DPI = 40
MAX_DPI = 200

#: Below 2 there is no mosaic left to speak of.
MIN_MOSAIC_BLOCK = 2
MAX_MOSAIC_BLOCK = 64


def _session_source(sid):
    """Path of a session's uploaded PDF, or None if the session is unusable."""
    if not redact_session.is_valid_sid(sid):
        return None
    return redact_session.source_path(Config.UPLOAD_FOLDER, sid)


def _json_body():
    """The parsed request body, or None when it is not a JSON object."""
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None


@pdf_redact_bp.route("/api/v1/pdf-redact/open", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def pdf_redact_open():
    sid = None
    try:
        f = request.files.get("file")
        if f is None or not f.filename:
            return jsonify({"error": _("No file provided")}), 400

        filename = validate_filename(f.filename, Config.PDF_EXTENSIONS)
        # Nothing else sweeps the TTL: a session whose visitor simply closed the
        # tab would otherwise sit on disk forever, so collect on the way in.
        redact_session.cleanup_expired(Config.UPLOAD_FOLDER)
        # Streamed straight into its own session directory — the upload is the
        # only copy, and nothing about it is held in memory or in process state.
        sid = redact_session.create_session(Config.UPLOAD_FOLDER, filename, f.stream)
        source = redact_session.source_path(Config.UPLOAD_FOLDER, sid)

        # Header check runs on what actually landed on disk, so a renamed .exe
        # cannot pass by claiming to be a PDF.
        validate_file_security(source, filename)

        result = inspect_pdf(source, max_pages=MAX_PAGES)
        if not result.success:
            redact_session.delete_session(Config.UPLOAD_FOLDER, sid)
            return jsonify({"error": result.message}), 400

        return jsonify({
            "success": True,
            "session": sid,
            "original_name": filename,
            "page_count": result.data["page_count"],
            "pages": result.data["pages"],
        })
    except ValueError as e:
        redact_session.delete_session(Config.UPLOAD_FOLDER, sid)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        redact_session.delete_session(Config.UPLOAD_FOLDER, sid)
        return jsonify({"error": str(e)}), 500


@pdf_redact_bp.route("/api/v1/pdf-redact/page/<sid>/<int:page_no>")
@rate_limit(max_requests=200, window_seconds=60)
def pdf_redact_page(sid: str, page_no: int):
    source = _session_source(sid)
    if not source:
        return jsonify({"error": _("Session not found")}), 404

    try:
        dpi = int(request.args.get("dpi", DEFAULT_DPI))
    except (TypeError, ValueError):
        return jsonify({"error": _("Invalid DPI for page rendering")}), 400
    if not MIN_DPI <= dpi <= MAX_DPI:
        return jsonify({
            "error": _(
                "DPI must be between %(lo)s and %(hi)s",
                lo=MIN_DPI,
                hi=MAX_DPI,
            )
        }), 400

    import pymupdf

    try:
        doc = pymupdf.open(source)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        if not 1 <= page_no <= doc.page_count:
            return jsonify({"error": _("Page out of range")}), 400
        png = doc[page_no - 1].get_pixmap(dpi=dpi).tobytes("png")
    finally:
        doc.close()

    response = send_file(
        io.BytesIO(png),
        mimetype="image/png",
        download_name=f"page-{page_no}.png",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@pdf_redact_bp.route("/api/v1/pdf-redact/search", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
def pdf_redact_search():
    body = _json_body()
    if body is None:
        return jsonify({"error": _("Request body must be valid JSON")}), 400

    source = _session_source(body.get("sid"))
    if not source:
        return jsonify({"error": _("Session not found")}), 404

    pages = body.get("pages")
    if pages is not None and not isinstance(pages, list):
        return jsonify({"error": _("Pages must be a list of page numbers")}), 400

    result = find_text_matches(
        source,
        body.get("pattern", ""),
        regex=bool(body.get("regex")),
        pages=pages,
    )
    if not result.success:
        return jsonify({"error": result.message}), 400

    return jsonify({"success": True, **result.data})


@pdf_redact_bp.route("/api/v1/pdf-redact/apply", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def pdf_redact_apply():
    body = _json_body()
    if body is None:
        return jsonify({"error": _("Request body must be valid JSON")}), 400

    source = _session_source(body.get("sid"))
    if not source:
        return jsonify({"error": _("Session not found")}), 404

    marks = body.get("marks")
    if not isinstance(marks, list) or not marks:
        return jsonify({"error": _("No regions were marked")}), 400

    block = body.get("mosaicBlock", DEFAULT_MOSAIC_BLOCK)
    try:
        block = int(block)
    except (TypeError, ValueError):
        return jsonify({"error": _("Mosaic block size must be a whole number")}), 400
    if not MIN_MOSAIC_BLOCK <= block <= MAX_MOSAIC_BLOCK:
        return jsonify({
            "error": _(
                "Mosaic block size must be between %(lo)s and %(hi)s",
                lo=MIN_MOSAIC_BLOCK,
                hi=MAX_MOSAIC_BLOCK,
            )
        }), 400

    output = redact_session.output_path(Config.UPLOAD_FOLDER, body["sid"])
    result = redact_pdf(source, output, marks, block)
    if not result.success:
        return jsonify({"error": result.message}), 400

    data = result.data
    leftover = data["leftover_regions"]
    return jsonify({
        "success": True,
        "page_count": data["page_count"],
        "total_marks": data["total_marks"],
        "applied": data["applied"],
        "image_marks": data["image_marks"],
        "leftover_regions": leftover,
        "verified": not leftover,
    })


@pdf_redact_bp.route("/api/v1/pdf-redact/download/<sid>")
@rate_limit(max_requests=30, window_seconds=60)
def pdf_redact_download(sid: str):
    if not redact_session.is_valid_sid(sid):
        return jsonify({"error": _("Session not found")}), 404

    output = redact_session.output_path(Config.UPLOAD_FOLDER, sid)
    meta = redact_session.load_meta(Config.UPLOAD_FOLDER, sid)
    if not output or not meta or not os.path.isfile(output):
        return jsonify({"error": _("Nothing to download for this session")}), 404

    stem = safe_download_name(os.path.splitext(meta.get("original_name", ""))[0]) or "document"

    @after_this_request
    def _cleanup(response):
        # The redacted copy has been handed over — nothing from this session
        # may outlive the download.
        redact_session.delete_session(Config.UPLOAD_FOLDER, sid)
        return response

    response = send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"redacted_{stem}.pdf",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@pdf_redact_bp.route("/api/v1/pdf-redact/close", methods=["POST"])
@rate_limit(max_requests=60, window_seconds=60)
def pdf_redact_close():
    body = _json_body()
    if body is None:
        return jsonify({"error": _("Request body must be valid JSON")}), 400

    sid = body.get("sid")
    if not redact_session.is_valid_sid(sid):
        return jsonify({"error": _("Invalid session id")}), 400

    redact_session.delete_session(Config.UPLOAD_FOLDER, sid)
    return jsonify({"success": True})
