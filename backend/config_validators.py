"""Configuration value validators.

Validates environment-driven settings at startup to catch misconfiguration
early (fail-fast), rather than failing deep in application logic.
"""

import os
import re
from urllib.parse import urlparse


def validate_db_url(url: str) -> bool:
    """Validate a database connection URL."""
    if not url:
        return False
    if url.startswith("sqlite:///"):
        return len(url) > len("sqlite:///")
    parsed = urlparse(url)
    return parsed.scheme in ("mysql", "postgresql", "mysql+pymysql") and bool(parsed.hostname)


def validate_broker_url(url: str) -> bool:
    """Validate a Celery broker URL."""
    if url == "memory://":
        return True
    parsed = urlparse(url)
    return parsed.scheme in ("redis", "amqp", "amqps") and bool(parsed.hostname)


def validate_cors_origins(origins: str) -> list[str]:
    """Parse and validate a comma-separated CORS origins string."""
    if not origins or origins.strip() == "*":
        return ["*"]
    result = []
    for origin in origins.split(","):
        origin = origin.strip()
        if not origin:
            continue
        if re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
            result.append(origin)
            continue
        parsed = urlparse(origin)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid CORS origin scheme: '{origin}'")
        if not parsed.hostname:
            raise ValueError(f"Invalid CORS origin hostname: '{origin}'")
        result.append(origin)
    return result


def validate_port(value, field_name: str = "port") -> int:
    """Validate a port number is in the valid range 1-65535."""
    port = int(value)
    if not (1 <= port <= 65535):
        raise ValueError(f"{field_name} must be 1-65535, got {port}")
    return port


def validate_max_size(value, field_name: str = "max_size") -> int:
    """Validate a file size limit is positive."""
    size = int(value)
    if size <= 0:
        raise ValueError(f"{field_name} must be positive, got {size}")
    return size


def validate_writable_dir(path: str, create: bool = False) -> str:
    """Validate that a directory exists and is writable."""
    abs_path = os.path.abspath(path)
    if create:
        os.makedirs(abs_path, mode=0o755, exist_ok=True)
    if not os.path.isdir(abs_path):
        raise ValueError(f"Not a directory: {abs_path}")
    if not os.access(abs_path, os.W_OK):
        raise ValueError(f"Directory not writable: {abs_path}")
    return abs_path


def validate_startup_config(config_obj) -> list[str]:
    """Run all config validations at startup. Returns list of warnings."""
    warnings = []
    upload = config_obj.get("UPLOAD_FOLDER", "")
    try:
        validate_writable_dir(upload, create=True)
    except ValueError as e:
        warnings.append(f"UPLOAD_FOLDER: {e}")
    origins = os.environ.get("DOCSTAMP_CORS_ORIGINS", "")
    if origins:
        try:
            validate_cors_origins(origins)
        except ValueError as e:
            warnings.append(f"CORS_ORIGINS: {e}")
    if not os.environ.get("DOCSTAMP_ENCRYPTION_KEY"):
        warnings.append("DOCSTAMP_ENCRYPTION_KEY not set; using auto-generated key")
    return warnings
