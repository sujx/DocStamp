"""Temporary file cleanup via scheduled task.

Replaces the old @after_this_request immediate-deletion pattern.
Files are kept for 7 days to allow:
- Debugging failed operations
- Re-downloading previous results
- Auditing operation logs against file artifacts
"""

import logging
import os
import time

logger = logging.getLogger(__name__)


def cleanup_temp_files(upload_folder: str, max_age_days: int = 7) -> dict:
    """Delete temporary files older than max_age_days.

    Designed to be called by Celery Beat or external cron:
        celery.conf.beat_schedule = {
            "cleanup-temp": {
                "task": "backend.tasks.maintenance.cleanup_temp_files",
                "schedule": crontab(hour=3, minute=0),
            },
        }

    Args:
        upload_folder: Directory containing temporary files.
        max_age_days: Files older than this many days are deleted.

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
        fpath = os.path.join(upload_folder, fname)
        try:
            if not os.path.isfile(fpath):
                continue
            if os.path.getmtime(fpath) < cutoff:
                fsize = os.path.getsize(fpath)
                os.remove(fpath)
                deleted += 1
                freed += fsize
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
