"""Gunicorn production configuration for docStamp.

Optimised for ~100 concurrent users behind an nginx reverse proxy.
Uses gthread workers so a single worker can handle multiple connections
while slow document-processing requests are in flight.
"""

import multiprocessing

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
