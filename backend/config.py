"""Unified application configuration.

Extracted from app.py to keep the factory lean.
All environment-variable-driven settings have sensible defaults.
"""

import os


class Config:
    """Application configuration for docStamp Flask backend."""

    # ── File Storage ────────────────────────────────────────────────
    UPLOAD_FOLDER = os.environ.get(
        "DOCSTAMP_UPLOAD_FOLDER",
        os.path.join(os.path.dirname(__file__), "output"),
    )
    MAX_CONTENT_LENGTH = 110 * 1024 * 1024  # 110 MB — Flask-level request body cap
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB (legacy, prefer file_security.MAX_FILE_SIZE)
    MAX_MD_SIZE = 16 * 1024 * 1024  # 16 MB

    # ── Allowed Extensions per Feature ──────────────────────────────
    OFFICE_EXTENSIONS = {"docx", "xlsx", "pptx"}
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "tiff", "tif"}
    PDF_EXTENSIONS = {"pdf"}
    WATERMARK_EXTENSIONS = {"docx", "pdf"}
    EXCEL_EXTENSIONS = {"xlsx", "csv"}
    MD_EXTENSIONS = {"md", "markdown", "txt"}
    VIDEO_EXTENSIONS = {"mp4", "wmv", "avi", "mkv", "mov"}
    DOWNLOAD_EXTENSIONS = {"docx", "md", "wmv"}

    # ── Security ────────────────────────────────────────────────────
    FORBIDDEN_PATH_CHARS = {"..", "/", "\\"}
    SECRET_KEY = os.environ.get("DOCSTAMP_SECRET_KEY", "dev-secret-change-in-production")

    # ── Celery ──────────────────────────────────────────────────────
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "db+sqlite:///tasks.db"
    )

    # ── Task DB ─────────────────────────────────────────────────────
    TASK_DB_PATH = os.environ.get(
        "DOCSTAMP_TASK_DB",
        os.path.join(os.path.dirname(__file__), "tasks.db"),
    )

    # ── Cache ───────────────────────────────────────────────────────
    CACHE_TYPE = os.environ.get("DOCSTAMP_CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("DOCSTAMP_CACHE_TTL", "300"))

    # ── Encryption ──────────────────────────────────────────────────
    ENCRYPTION_KEY = os.environ.get("DOCSTAMP_ENCRYPTION_KEY", "")

    # ── AI ──────────────────────────────────────────────────────────
    AI_API_KEY = os.environ.get("DOCSTAMP_DEEPSEEK_API_KEY", "")
    MINERU_API_KEY = os.environ.get("DOCSTAMP_MINERU_API_KEY", "")
    AI_API_URL = os.environ.get(
        "AI_API_URL", "https://api.deepseek.com/chat/completions"
    )
    AI_MODEL = os.environ.get("AI_MODEL", "deepseek-v4-flash")

    # ── Company Lookup (web search via LLM) ─────────────────────────
    # Uses Zhipu BigModel web search by default. Falls back to
    # DOCSTAMP_DEEPSEEK_API_KEY + AI_API_URL if not set.
    COMPANY_LOOKUP_API_KEY = os.environ.get(
        "COMPANY_LOOKUP_API_KEY", os.environ.get("DOCSTAMP_DEEPSEEK_API_KEY", "")
    )
    COMPANY_LOOKUP_API_URL = os.environ.get(
        "COMPANY_LOOKUP_API_URL",
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    )
    COMPANY_LOOKUP_MODEL = os.environ.get(
        "COMPANY_LOOKUP_MODEL", "glm-4-flash"
    )

    # ── Frontend Static ─────────────────────────────────────────────
    STATIC_FOLDER = os.environ.get(
        "DOCSTAMP_STATIC",
        os.path.join(os.path.dirname(__file__), "..", "frontend", ".output", "public"),
    )

    # ── Logging ─────────────────────────────────────────────────────
    LOG_LEVEL = int(os.environ.get("DOCSTAMP_LOG_LEVEL", "20"))  # INFO
    LOG_DIR = os.environ.get("DOCSTAMP_LOG_DIR", "/var/log/docstamp")

    # ── i18n ────────────────────────────────────────────────────────
    LANGUAGES = ["en", "zh_CN"]
    BABEL_DEFAULT_LOCALE = "en"
