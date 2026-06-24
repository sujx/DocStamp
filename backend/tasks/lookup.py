"""convert_queue tasks: Company lookup batch processing.

Batch company name → website lookups run asynchronously so large lists
don't block the HTTP request. Progress is streamed via TaskRecord → SSE.
"""

import json

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
            task_id, "progress", progress_message=f"Retrying: {exc}",
        )


@celery.task(base=TrackedTask, bind=True, queue="convert_queue")
def company_lookup_batch(self, names: list[str]):
    """Asynchronously look up websites for a batch of company names.

    Each name is checked against the local DB first, then searched via
    web if not found. Results are accumulated and stored in result_data.
    """
    _record.create_task(self.request.id, "company_lookup_batch", "convert_queue")
    _record.update_progress(
        self.request.id, "started", progress=0,
        progress_message=f"Starting batch lookup for {len(names)} companies...",
    )

    from backend.services.company_lookup import batch_lookup

    total = len(names)
    db_path = _get_db_path()
    results: list[dict] = []

    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            results.append({"name": "", "website": "", "source": "error", "error": "Empty name"})
            continue

        progress = int((i + 1) / total * 90)  # Reserve 90% for processing, last 10% for finalizing
        _record.update_progress(
            self.request.id, "progress", progress=progress,
            progress_message=f"Looking up ({i + 1}/{total}): {name}",
        )

    # Run the actual batch lookup
    results = batch_lookup(names, db_path)

    _record.update_progress(
        self.request.id, "progress", progress=95,
        progress_message="Finalizing results...",
    )

    result_json = json.dumps(results, ensure_ascii=False)
    local_count = sum(1 for r in results if r.get("source") == "local")
    web_count = sum(1 for r in results if r.get("source") == "web")
    error_count = sum(1 for r in results if r.get("source") == "error" or r.get("error"))

    _record.update_progress(
        self.request.id, "success", progress=100,
        progress_message=f"Done: {local_count} local, {web_count} web, {error_count} not found",
        result_data=result_json,
    )

    return {
        "total": total,
        "local": local_count,
        "web": web_count,
        "errors": error_count,
        "results": results,
    }
