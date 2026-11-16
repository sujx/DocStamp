"""Meeting minutes (纪要) generation route — GB/T 9704-2012 clause 10.3.

一次性下载形态（抄 webp_to_jpeg_bp.py），不走 convert.py 的 download_id 两段式：
宣传页的「响应结束即删」承诺要求产物在响应后消失。
"""

import os
import uuid

from flask import Blueprint, after_this_request, jsonify, send_file

from config import Config
from error_handler import validate_request
from schemas import MeetingMinutesSchema
from services.minutes_docx import build_minutes
from utils.base.file_helpers import cleanup_files, safe_download_name
from utils.rate_limit import rate_limit

meeting_minutes_bp = Blueprint("meeting_minutes", __name__)

DOCX_MIMETYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@meeting_minutes_bp.route("/api/v1/meeting-minutes", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
@validate_request(body=MeetingMinutesSchema)
def meeting_minutes(body: MeetingMinutesSchema):
    output_path = os.path.join(Config.UPLOAD_FOLDER, f"{uuid.uuid4().hex}.docx")
    try:
        result = build_minutes(body.model_dump(), output_path)
        if not result.success:
            cleanup_files(output_path)
            return jsonify({"error": result.message}), 400

        @after_this_request
        def _cleanup(response):
            cleanup_files(output_path)
            return response

        return send_file(
            output_path,
            mimetype=DOCX_MIMETYPE,
            as_attachment=True,
            download_name=f"{safe_download_name(body.meet_name)}纪要.docx",
        )
    except Exception as e:
        cleanup_files(output_path)
        return jsonify({"error": str(e)}), 500
