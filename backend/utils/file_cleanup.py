"""Temporary file cleanup via scheduled task.

Replaces the old @after_this_request immediate-deletion pattern.
Files are kept for 7 days to allow:
- Debugging failed operations
- Re-downloading previous results
- Auditing operation logs against file artifacts
"""

import logging
import os
import shutil
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CLEANUP_CHECK_SECONDS = 3600
CLEANUP_INTERVAL_SECONDS = 24 * 3600
CLEANUP_MAX_AGE_DAYS = 7
CLEANUP_STAMP_NAME = ".cleanup-stamp"

# The upload folder doubles as the home of live state: the stats counter is
# rewritten on every conversion, and .gitkeep keeps the directory in version
# control.  Neither may ever be aged out.
PRESERVED_NAMES = {".stats", ".gitkeep"}


def _tree_stats(path: str) -> tuple[int, int]:
    """Return (file_count, total_bytes) for a file or a directory tree."""
    if os.path.isfile(path):
        return 1, os.path.getsize(path)

    files = 0
    size = 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            try:
                files += 1
                size += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return files, size


def cleanup_temp_files(upload_folder: str, max_age_days: int = 7) -> dict:
    """Delete temporary files and directories older than max_age_days.

    Per-task output directories (pdf2img_*, thumbs_*, print-split task dirs,
    properties batch dirs) are removed recursively with their contents.

    Designed to be called once a day by the cleanup daemon started from
    gunicorn's on_starting hook (see gunicorn.conf.py), or by an external
    cron job.

    Args:
        upload_folder: Directory containing temporary files.
        max_age_days: Entries older than this many days are deleted.

    Returns:
        dict with keys: deleted_count, freed_bytes, errors.
    """
    if not os.path.isdir(upload_folder):
        logger.warning("Upload folder does not exist: %s", upload_folder)
        return {"deleted_count": 0, "freed_bytes": 0, "errors": 0}

    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    freed = 0
    error_count = 0

    for fname in os.listdir(upload_folder):
        if fname in PRESERVED_NAMES:
            continue
        fpath = os.path.join(upload_folder, fname)
        try:
            if os.path.getmtime(fpath) >= cutoff:
                continue
            files, size = _tree_stats(fpath)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
            else:
                os.remove(fpath)
            deleted += files or 1
            freed += size
        except OSError as e:
            logger.warning("Failed to delete %s: %s", fpath, e)
            error_count += 1

    if deleted:
        logger.info(
            "Cleaned %d temp files, freed %d bytes, %d errors",
            deleted, freed, error_count,
        )

    return {
        "deleted_count": deleted,
        "freed_bytes": freed,
        "errors": error_count,
    }


# ── Daily scheduling ─────────────────────────────────────────────────

def _write_stamp(stamp_path, when: datetime) -> None:
    try:
        with open(stamp_path, "w", encoding="utf-8") as f:
            f.write(when.isoformat())
    except OSError as e:
        logger.warning("could not write cleanup stamp %s: %s", stamp_path, e)


def cleanup_due(stamp_path, now: datetime = None,
                interval_seconds: int = CLEANUP_INTERVAL_SECONDS) -> bool:
    """True when the last cleanup is older than interval_seconds (or unknown)."""
    now = now or datetime.now(timezone.utc)
    try:
        with open(stamp_path, encoding="utf-8") as f:
            last = datetime.fromisoformat(f.read().strip())
    except (OSError, ValueError):
        return True
    return (now - last).total_seconds() >= interval_seconds


def run_cleanup(upload_folder: str, stamp_path, now: datetime = None) -> None:
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


def start_cleanup_daemon(upload_folder: str, stamp_path) -> threading.Thread:
    thread = threading.Thread(
        target=_cleanup_loop, args=(upload_folder, stamp_path),
        name="cleanup", daemon=True,
    )
    thread.start()
    return thread
