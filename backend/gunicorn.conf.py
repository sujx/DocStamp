"""Gunicorn production configuration for docStamp.

Optimised for ~100 concurrent users behind an nginx reverse proxy.
Uses gthread workers so a single worker can handle multiple connections
while slow document-processing requests are in flight.
"""

import multiprocessing
import os
import sys

bind = "127.0.0.1:5000"          # Only reachable via reverse proxy
worker_class = "gthread"
threads = 4                       # Concurrent connections per worker
workers = min(8, multiprocessing.cpu_count() * 2 + 1)
timeout = 120
keepalive = 5                     # Reuse keep-alive connections
max_requests = 1000               # Recycle workers to bound memory leaks
max_requests_jitter = 100

loglevel = "info"
accesslog = "/var/log/docstamp/access.log"
errorlog = "/var/log/docstamp/error.log"
pidfile = "/var/run/docstamp.pid"

# Preload app before forking workers — ensures DB / caches are initialised once
preload_app = True


def on_starting(server):
    """Start the daily temp-file cleanup daemon in the master process.

    Runs once before workers fork, so the whole deployment gets exactly one
    cleanup thread regardless of the worker count.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from config import Config
    from utils.file_cleanup import CLEANUP_STAMP_NAME, start_cleanup_daemon

    stamp_path = os.path.join(
        os.path.dirname(os.path.abspath(Config.TASK_DB_PATH)), CLEANUP_STAMP_NAME
    )
    start_cleanup_daemon(Config.UPLOAD_FOLDER, stamp_path)
