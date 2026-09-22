"""Celery application configuration for docStamp async task processing.

Broker: Redis (production default) — set CELERY_BROKER_URL to override.
Two queues, both served by the single worker container in docker-compose:
    - pdf_queue:      video conversion (MP4 → WMV)
    - office_queue:   scheduled maintenance (temp file cleanup)

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
        "backend.tasks.video",
        "backend.tasks.maintenance",
    ],

    # Queue routing
    task_routes={
        "backend.tasks.video.*":    {"queue": "pdf_queue"},
    },

    # Result expiry — baseline for all tasks; individual tasks override it in
    # their @celery.task(result_expires=...) decorator.
    result_expires=12 * 3600,   # Default: 12 hours

    # Worker settings
    worker_concurrency=4,       # Raised from 2 for production throughput
    task_track_started=True,
    task_acks_late=True,        # Ack AFTER task completes — no lost tasks
    task_reject_on_worker_lost=True,

    # Beat schedule
    beat_schedule={
        "cleanup-temp-files": {
            "task": "backend.tasks.maintenance.cleanup_temp_files_task",
            "schedule": crontab(hour=3, minute=0),
        },
    },

    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,
)

# Worker startup commands (run from project root):
#   celery -A backend.celery_app worker -Q pdf_queue,office_queue --concurrency=2 -B
#   celery -A backend.celery_app beat   (scheduler, standalone)
