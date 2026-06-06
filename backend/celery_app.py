"""Celery application configuration for docStamp async task processing.

Broker: memory:// (development) — set CELERY_BROKER_URL for production.
Three queues with independent worker processes to prevent resource contention:
    - convert_queue: MD → DOCX conversion, DOCX formatting
    - pdf_queue:      Watermark, print split, PDF edit, img2pdf, pdf2img
    - office_queue:   Properties modification, Excel merge

Beat schedule: daily cleanup of temp files older than 7 days.
"""

from celery import Celery
from celery.schedules import crontab

celery = Celery("docstamp")

celery.conf.update(
    # Broker & backend
    broker_url="memory://",
    result_backend="db+sqlite:///tasks.db",

    # Queue routing
    task_routes={
        "backend.tasks.convert.*":  {"queue": "convert_queue"},
        "backend.tasks.pdf.*":      {"queue": "pdf_queue"},
        "backend.tasks.office.*":   {"queue": "office_queue"},
    },

    # Worker settings
    worker_concurrency=2,
    task_track_started=True,
    task_acks_late=True,

    # Beat schedule
    beat_schedule={
        "cleanup-temp-files": {
            "task": "backend.tasks.maintenance.cleanup_temp_files",
            "schedule": crontab(hour=3, minute=0),
        },
    },

    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,
)

# Worker startup commands (run from project root):
#   celery -A backend.celery_app worker -Q convert_queue --concurrency=2 -n convert@%h
#   celery -A backend.celery_app worker -Q pdf_queue --concurrency=2 -n pdf@%h
#   celery -A backend.celery_app worker -Q office_queue --concurrency=2 -n office@%h
#   celery -A backend.celery_app beat   (scheduler)
