"""WSGI entry point for Gunicorn / production servers.

This file exists solely to provide a module-level `app` variable
so that Gunicorn can import it as `backend.wsgi:app`.

app.py exposes create_app() as a factory — it should never be
imported at module level (doing so triggers Flask instantiation,
SQLite connection, and blueprint registration as a side effect).

The project root is added to sys.path so that `from backend.xxx`
imports work regardless of the working directory (Gunicorn is
started from backend/, but some blueprints use absolute `backend.`
prefix imports).
"""

import os
import sys

# Ensure the project root is on sys.path so that `from backend.xxx`
# imports resolve correctly regardless of CWD.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app import create_app

app = create_app()
