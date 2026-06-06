"""Celery Beat scheduled maintenance tasks."""

import os

from backend.celery_app import celery
from backend.utils.file_cleanup import cleanup_temp_files


@celery.task(queue="office_queue")
def cleanup_temp_files_task():
    """Daily cleanup: delete temp files older than 7 days.

    Scheduled by Celery Beat: crontab(hour=3, minute=0)
    """
    from backend.config import Config

    upload_folder = Config().UPLOAD_FOLDER
    if not os.path.isdir(upload_folder):
        return {"status": "skipped", "reason": "upload folder not found"}

    result = cleanup_temp_files(upload_folder, max_age_days=7)
    result["status"] = "ok"
    return result
