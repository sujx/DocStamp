"""Celery async task: video conversion (MP4 → WMV)."""

import json
import os

from celery import Task
from celery_app import celery

from models import TaskRecord

_record = None


def _get_record():
    global _record
    if _record is None:
        import os as _os
        _record = TaskRecord(_os.environ.get(
            "DOCSTAMP_TASK_DB",
            _os.path.join(_os.path.dirname(__file__), "..", "tasks.db"),
        ))
    return _record


class TrackedTask(Task):
    """Updates TaskRecord on success/failure/retry — same as convert.py."""
    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        r = _get_record()
        try:
            r.update_progress(task_id, "success", progress=100)
        except Exception:
            pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        r = _get_record()
        try:
            r.update_progress(
                task_id, "failure",
                error_code="TASK_FAILED",
                error_message=str(exc),
            )
        except Exception:
            pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        r = _get_record()
        try:
            r.update_progress(
                task_id, "progress",
                progress_message=f"Retrying: {exc}",
            )
        except Exception:
            pass


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue")
def video_convert_async(self, input_path: str, output_path: str, original_name: str):
    """Convert a video to WMV format (async, with progress)."""
    record = _get_record()
    record.create_task(self.request.id, "video_convert", "pdf_queue")

    record.update_progress(self.request.id, "started", progress=0,
                           progress_message="Preparing video...")

    from services.video_converter import mp4_to_wmv

    record.update_progress(self.request.id, "progress", progress=20,
                           progress_message="Converting with ffmpeg...")

    result = mp4_to_wmv(input_path, output_path)

    if not result.success:
        record.update_progress(
            self.request.id, "failure", progress=0,
            error_code="CONVERSION_FAILED",
            error_message=result.message,
        )
        return {"error": result.message}

    record.update_progress(self.request.id, "progress", progress=90,
                           progress_message="Finalizing...")

    base = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
    download_name = f"{base}.wmv"
    file_size = os.path.getsize(output_path)

    record.update_progress(
        self.request.id, "success", progress=100,
        result_data=json.dumps({
            "filename": download_name,
            "download_id": os.path.basename(output_path),
            "size": file_size,
        }),
    )

    return {"filename": download_name, "size": file_size}
