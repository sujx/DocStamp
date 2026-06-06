"""convert_queue tasks: MD → DOCX conversion and DOCX formatting.

These tasks are CPU-bound (Pandoc subprocess) and routed to convert_queue
to avoid blocking PDF and office operations.
"""

import json
import os
import uuid

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
        _record.update_progress(task_id, "success", progress=100)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        _record.update_progress(
            task_id, "failure", error_code="TASK_FAILED", error_message=str(exc),
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        _record.update_progress(
            task_id, "progress", progress_message=f"正在重试: {exc}",
        )


@celery.task(base=TrackedTask, bind=True, queue="convert_queue")
def md_to_docx_async(self, md_path: str, output_path: str):
    """Asynchronously convert Markdown to GB/T 9704-2012 DOCX."""
    _record.create_task(self.request.id, "md_to_docx", "convert_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在解析 Markdown...")

    from backend.converter import md_to_docx
    title = md_to_docx(md_path, output_path)

    _record.update_progress(self.request.id, "progress", progress=60,
                           progress_message="正在应用 GB/T 9704-2012 格式...")

    from backend.formatter import format_docx
    format_docx(output_path)

    _record.update_progress(
        self.request.id, "success", progress=100,
        result_data=json.dumps({"filename": f"{title}.docx", "title": title}),
    )

    return {"filename": f"{title}.docx", "title": title}


@celery.task(base=TrackedTask, bind=True, queue="convert_queue")
def format_docx_async(self, filepath: str, output_path: str, original_name: str):
    """Asynchronously format an existing DOCX per GB/T 9704-2012."""
    _record.create_task(self.request.id, "format_docx", "convert_queue")
    _record.update_progress(self.request.id, "started", progress=0,
                           progress_message="正在格式化 DOCX...")

    import shutil
    shutil.copy2(filepath, output_path)

    from backend.formatter import format_docx
    format_docx(output_path)

    title = original_name.rsplit(".", 1)[0] if original_name else "document"
    _record.update_progress(
        self.request.id, "success", progress=100,
        result_data=json.dumps({"filename": f"{title}.docx", "title": title}),
    )

    return {"filename": f"{title}.docx", "title": title}
