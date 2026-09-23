"""Task worker: consumes the SQLite work queue in task_records.

Polls for pending rows, claims each with an atomic UPDATE, and runs the
conversion in-process. Progress and results land in the same table the SSE
endpoint already reads, so the frontend never sees the executor.

Started by docker-compose as `python -m backend.worker`, and by manage.sh in
dev mode. A daemon thread performs the daily temp-file cleanup.
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Optional

# The bare imports below need backend/ itself on sys.path, but `-m` only puts
# the project root there (Docker and manage.sh both launch it that way).
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_backend_dir)
for _path in (_backend_dir, _project_root):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from config import Config  # noqa: E402
from errors import ErrorCode  # noqa: E402
from models import TaskRecord, init_db  # noqa: E402
from services.video_converter import mp4_to_wmv  # noqa: E402
from utils.file_cleanup import cleanup_temp_files  # noqa: E402

logger = logging.getLogger("docstamp.worker")

POLL_INTERVAL_SECONDS = 1.0
CLEANUP_CHECK_SECONDS = 3600
CLEANUP_INTERVAL_SECONDS = 24 * 3600
CLEANUP_MAX_AGE_DAYS = 7
CLEANUP_STAMP_NAME = ".cleanup-stamp"


# ── Daily temp-file cleanup ─────────────────────────────────────────

def _write_stamp(stamp_path, when: datetime) -> None:
    try:
        with open(stamp_path, "w", encoding="utf-8") as f:
            f.write(when.isoformat())
    except OSError as e:
        logger.warning("could not write cleanup stamp %s: %s", stamp_path, e)


def cleanup_due(stamp_path, now: Optional[datetime] = None,
                interval_seconds: int = CLEANUP_INTERVAL_SECONDS) -> bool:
    """True when the last cleanup is older than interval_seconds (or unknown)."""
    now = now or datetime.now(timezone.utc)
    try:
        with open(stamp_path, encoding="utf-8") as f:
            last = datetime.fromisoformat(f.read().strip())
    except (OSError, ValueError):
        return True
    return (now - last).total_seconds() >= interval_seconds


def run_cleanup(upload_folder: str, stamp_path, now: Optional[datetime] = None) -> None:
    now = now or datetime.now(timezone.utc)
    if not os.path.isdir(upload_folder):
        logger.warning("upload folder missing, skipping cleanup: %s", upload_folder)
        return
    result = cleanup_temp_files(upload_folder, max_age_days=CLEANUP_MAX_AGE_DAYS)
    _write_stamp(stamp_path, now)
    logger.info("temp cleanup: %s", result)


def _cleanup_loop(upload_folder: str, stamp_path) -> None:
    """Runs the cleanup once at startup if it is overdue, then hourly checks."""
    while True:
        try:
            if cleanup_due(stamp_path):
                run_cleanup(upload_folder, stamp_path)
        except Exception:
            logger.exception("temp cleanup failed")
        time.sleep(CLEANUP_CHECK_SECONDS)


# ── Task execution ──────────────────────────────────────────────────

def recover_stale_tasks(record: TaskRecord) -> int:
    """Fail rows a previous worker died on, so the SSE stream can terminate.

    Without this a crashed conversion leaves the record parked at 'progress'
    and the frontend spinner never stops.
    """
    stale = record.list_stale()
    for row in stale:
        record.update_progress(
            row["id"], "failure", error_code="TASK_INTERRUPTED",
            error_message="Worker restarted, task interrupted — please submit again",
        )
    return len(stale)


def execute_task(record: TaskRecord, task_id: str, upload_folder: str) -> None:
    """Run one already-claimed task to a terminal state.

    Conversion failures are recorded on the row rather than raised, so one bad
    task cannot stop the queue; only a DB-level error can still propagate.
    """
    row = record.get_by_id(task_id)
    try:
        payload = json.loads(row["result_data"] or "{}")
        input_name = payload["input"]
        output_name = payload["output"]
    except (KeyError, TypeError, ValueError):
        record.update_progress(
            task_id, "failure", error_code="TASK_FAILED",
            error_message="Task payload missing or corrupt — please upload again",
        )
        return

    input_path = os.path.join(upload_folder, input_name)
    output_path = os.path.join(upload_folder, output_name)

    if not os.path.isfile(input_path):
        record.update_progress(
            task_id, "failure", error_code="FILE_NOT_FOUND",
            error_message="Source file no longer exists — please upload again",
        )
        return

    try:
        # progress_message carries locale-neutral stage codes; the frontend
        # maps them to videoConvert.progress.* i18n keys.
        record.update_progress(task_id, "started", progress=0,
                               message="preparing")
        record.update_progress(task_id, "progress", progress=20,
                               message="converting")

        result = mp4_to_wmv(input_path, output_path)

        if not result.success:
            record.update_progress(
                task_id, "failure", progress=0,
                error_code=result.error.value if result.error
                else ErrorCode.CONVERSION_FAILED.value,
                error_message=result.message,
            )
            return

        record.update_progress(task_id, "progress", progress=90,
                               message="finalizing")

        base = input_name.rsplit(".", 1)[0] if "." in input_name else input_name
        record.update_progress(
            task_id, "success", progress=100,
            result_data=json.dumps({
                "filename": f"{base}.wmv",
                "download_id": os.path.basename(output_path),
                "size": os.path.getsize(output_path),
            }),
        )
    except Exception as e:
        logger.exception("task %s failed", task_id)
        record.update_progress(
            task_id, "failure", error_code="TASK_FAILED", error_message=str(e),
        )


def run_pending_once(record: TaskRecord, upload_folder: str) -> int:
    """Drain the queue. Returns the number of tasks claimed and executed."""
    processed = 0
    while True:
        row = record.next_pending()
        if row is None:
            return processed
        if not record.claim(row["id"]):
            continue
        processed += 1
        execute_task(record, row["id"], upload_folder)


# ── Entry point ─────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )

    db_path = Config.TASK_DB_PATH
    upload_folder = Config.UPLOAD_FOLDER
    init_db(db_path)
    os.makedirs(upload_folder, exist_ok=True)
    stamp_path = os.path.join(os.path.dirname(os.path.abspath(db_path)),
                              CLEANUP_STAMP_NAME)

    record = TaskRecord(db_path)
    recovered = recover_stale_tasks(record)
    if recovered:
        logger.warning("recovered %d interrupted task(s)", recovered)

    threading.Thread(
        target=_cleanup_loop, args=(upload_folder, stamp_path),
        name="cleanup", daemon=True,
    ).start()

    logger.info("worker ready (db=%s, upload=%s)", db_path, upload_folder)
    while True:
        try:
            run_pending_once(record, upload_folder)
        except Exception:
            logger.exception("poll loop error")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
