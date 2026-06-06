"""Gunicorn production configuration for docStamp."""

bind = "127.0.0.1:5000"
workers = 4
timeout = 120
loglevel = "info"
accesslog = "/var/log/docstamp/access.log"
errorlog = "/var/log/docstamp/error.log"
pidfile = "/var/run/docstamp.pid"
