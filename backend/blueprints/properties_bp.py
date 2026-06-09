"""Properties modification routes."""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, request, send_file
from flask_babel import gettext as _

from config import Config
from utils.base.file_helpers import cleanup_files, save_upload
from utils.rate_limit import rate_limit
from services.properties import _resolve_time_props, batch_modify_properties, modify_properties, read_properties

properties_bp = Blueprint("properties", __name__)


@properties_bp.route("/api/v1/properties/info", methods=["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def properties_info():
    filepath = None
    try:
        if "file" not in request.files:
            return jsonify({"error": _("No file provided")}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": _("No file selected")}), 400
        _name, filepath = save_upload(file, Config.OFFICE_EXTENSIONS, Config.UPLOAD_FOLDER)
        result = read_properties(filepath)
        if not result.success:
            return jsonify({"error": result.message}), 400
        return jsonify({"success": True, "properties": result.data})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_files(filepath)


@properties_bp.route("/api/v1/properties", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
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
        result = modify_properties(filepath, output_path, resolved)
        if not result.success:
            cleanup_files(filepath, output_path)
            return jsonify({"error": result.message}), 400

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


@properties_bp.route("/api/v1/properties/batch", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
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
        result = batch_modify_properties(filepaths, output_dir, props, unify_time)
        if not result.success:
            for p in filepaths:
                cleanup_files(p)
            return jsonify({"error": result.message}), 400
        results = result.data

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
