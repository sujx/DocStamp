"""WSGI entry point for Gunicorn / production servers.

This file exists solely to provide a module-level `app` variable
so that Gunicorn can import it as `backend.wsgi:app`.

app.py exposes create_app() as a factory — it should never be
imported at module level (doing so triggers Flask instantiation,
SQLite connection, and blueprint registration as a side effect).
"""

from app import create_app

app = create_app()
