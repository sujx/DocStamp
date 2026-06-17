"""Celery application configuration for docStamp async task processing.

Broker: Redis (production default) — set CELERY_BROKER_URL to override.
Three queues with independent worker processes to prevent resource contention:
    - convert_queue: MD → DOCX conversion, DOCX formatting
    - pdf_queue:      Watermark, print split, PDF edit, img2pdf, pdf2img
    - office_queue:   Properties modification, Excel merge

Beat schedule: daily cleanup of temp files older than 7 days.
"""

import os

from celery import Celery
from celery.schedules import crontab

celery = Celery("docstamp")

celery.conf.update(
    # Broker & backend — Redis for production, memory:// for dev
    broker_url=os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    result_backend=os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"
    ),
    broker_connection_retry_on_startup=True,

    # Import task modules so Celery registers @celery.task decorated functions
    include=[
        "backend.tasks.convert",
        "backend.tasks.pdf",
        "backend.tasks.office",
        "backend.tasks.video",
        "backend.tasks.maintenance",
    ],

    # Queue routing
    task_routes={
        "backend.tasks.convert.*":  {"queue": "convert_queue"},
        "backend.tasks.pdf.*":      {"queue": "pdf_queue"},
        "backend.tasks.office.*":   {"queue": "office_queue"},
        "backend.tasks.video.*":    {"queue": "pdf_queue"},
    },

    # Worker settings
    worker_concurrency=4,       # Raised from 2 for production throughput
    task_track_started=True,
    task_acks_late=True,        # Ack AFTER task completes — no lost tasks
    task_reject_on_worker_lost=True,

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
#   celery -A backend.celery_app worker -Q convert_queue --concurrency=4 -n convert@%h
#   celery -A backend.celery_app worker -Q pdf_queue --concurrency=4 -n pdf@%h
#   celery -A backend.celery_app worker -Q office_queue --concurrency=4 -n office@%h
#   celery -A backend.celery_app beat   (scheduler)
