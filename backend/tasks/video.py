"""Celery async task: video conversion (MP4 → WMV)."""

import json
import os

from celery import Task

from backend.celery_app import celery
from backend.models import TaskRecord

def _get_db_path():
    from backend.config import Config
    return Config().TASK_DB_PATH


_record = TaskRecord(_get_db_path())


class TrackedTask(Task):
    """Base task with TaskRecord lifecycle tracking."""

    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        # Task bodies that handle their own failures return an error dict rather
        # than raising, so don't let the success hook overwrite that terminal state.
        existing = _record.get_by_id(task_id)
        if existing and existing["status"] == "failure":
            return
        _record.update_progress(task_id, "success", progress=100)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        _record.update_progress(
            task_id, "failure", error_code="TASK_FAILED", error_message=str(exc),
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        _record.update_progress(
            task_id, "progress", message=f"正在重试: {exc}",
        )


@celery.task(base=TrackedTask, bind=True, queue="pdf_queue", result_expires=6 * 3600)
def video_convert_async(self, input_path: str, output_path: str, original_name: str):
    """Convert a video to WMV format (async, with progress)."""
    _record.create_task(self.request.id, "video_convert", "pdf_queue")

    _record.update_progress(self.request.id, "started", progress=0,
                           message="Preparing video...")

    from backend.services.video_converter import mp4_to_wmv

    _record.update_progress(self.request.id, "progress", progress=20,
                           message="Converting with ffmpeg...")

    result = mp4_to_wmv(input_path, output_path)

    if not result.success:
        _record.update_progress(
            self.request.id, "failure", progress=0,
            error_code="CONVERSION_FAILED",
            error_message=result.message,
        )
        return {"error": result.message}

    _record.update_progress(self.request.id, "progress", progress=90,
                           message="Finalizing...")

    base = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
    download_name = f"{base}.wmv"
    file_size = os.path.getsize(output_path)

    _record.update_progress(
        self.request.id, "success", progress=100,
        result_data=json.dumps({
            "filename": download_name,
            "download_id": os.path.basename(output_path),
            "size": file_size,
        }),
    )

    return {"filename": download_name, "size": file_size}
