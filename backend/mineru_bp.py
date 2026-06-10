"""MinerU document-to-Markdown — cloud API with async polling.

Flow: upload → save → serve URL → MinerU submit → poll → extract MD → return.
Supports PDF, DOC, DOCX, PPT, PPTX, PNG, JPG.  200MB / 200 pages max.
"""

import hashlib
import io
import json
import os
import time
import zipfile

from flask import Blueprint, jsonify, request, current_app

from cache import cache
from config import Config
from utils.base.file_helpers import cleanup_files, save_upload

mineru_bp = Blueprint("mineru", __name__)

MINERU_URL = "https://mineru.net/api/v4/extract/task"
ALLOWED_EXTS = {"pdf", "doc", "docx", "ppt", "pptx", "png", "jpg", "jpeg"}
POLL_INTERVAL = 3
MAX_POLLS = 60
CACHE_TTL = 86400


def _file_hash(filepath: str) -> str:
    return hashlib.sha256(
        (os.path.basename(filepath) + str(os.path.getsize(filepath))).encode()
    ).hexdigest()[:12]


@mineru_bp.route("/api/v1/doc-to-md", methods=["POST"])
def doc_to_md():
    """Convert document to Markdown via MinerU API."""
    if "file" not in request.files:
        return jsonify({"code": 400, "msg": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"code": 400, "msg": "Empty filename"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTS:
        return jsonify({"code": 400, "msg": f"Unsupported format: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTS))}"}), 400

    # Save file
    try:
        _fn, filepath = save_upload(file, ALLOWED_EXTS, Config.UPLOAD_FOLDER)
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400

    # Check cache
    cache_key = f"mineru:{_file_hash(filepath)}"
    cached = cache.get(cache_key)
    if cached:
        cleanup_files(filepath)
        return jsonify({"code": 200, "data": {"markdown": cached, "cached": True}})

    # Build public URL
    server_url = request.host_url.rstrip("/")
    filename = os.path.basename(filepath)
    file_url = f"{server_url}/api/v1/download/{filename}"

    if not Config.MINERU_API_KEY:
        cleanup_files(filepath)
        return jsonify({"code": 503, "msg": "MinerU API key not configured. Set DOCSTAMP_MINERU_API_KEY."}), 503

    import requests  # lazy — only needed when MinerU endpoint is called

    # Submit to MinerU
    try:
        resp = requests.post(
            MINERU_URL,
            headers={"Authorization": f"Bearer {Config.MINERU_API_KEY}"},
            json={
                "url": file_url,
                "model_version": "vlm",
                "is_ocr": True,
                "enable_formula": True,
                "enable_table": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        task = resp.json()
    except Exception as e:
        cleanup_files(filepath)
        return jsonify({"code": 502, "msg": f"MinerU submit failed: {e}"}), 502

    task_id = task.get("data", {}).get("task_id") or task.get("task_id")
    if not task_id:
        cleanup_files(filepath)
        return jsonify({"code": 502, "msg": "MinerU did not return task_id"}), 502

    # Poll
    md_content = None
    for attempt in range(MAX_POLLS):
        time.sleep(POLL_INTERVAL)
        try:
            sr = requests.get(
                f"{MINERU_URL}/{task_id}",
                headers={"Authorization": f"Bearer {Config.MINERU_API_KEY}"},
                timeout=10,
            )
            sr.raise_for_status()
            status = sr.json()
        except Exception:
            continue

        data = status.get("data", {})
        state = data.get("state", status.get("state", ""))
        if state in ("done", "success"):
            zip_url = data.get("full_zip_url") or data.get("download_url") or ""
            )
            if zip_url:
                try:
                    zr = requests.get(zip_url, timeout=120)
                    zr.raise_for_status()
                    with zipfile.ZipFile(io.BytesIO(zr.content)) as zf:
                        for name in zf.namelist():
                            if name.endswith(".md"):
                                md_content = zf.read(name).decode("utf-8", errors="replace")
                                break
                except Exception:
                    pass
            break
        elif state == "failed":
            break

    cleanup_files(filepath)

    if md_content:
        cache.set(cache_key, md_content, timeout=CACHE_TTL)
        return jsonify({"code": 200, "data": {"markdown": md_content}})

    return jsonify({"code": 502, "msg": "MinerU processing failed or timed out (3 min)"}), 502
