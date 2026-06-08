"""Simple in-memory rate limiter using Flask-Caching.

Provides a @rate_limit decorator that limits requests per IP within a
configurable time window. Intended for the public-deployment defence-in-depth
strategy — the nginx layer provides coarse limits, this provides per-endpoint
granularity.

Usage:
    from utils.rate_limit import rate_limit

    @app.route("/api/image-process", methods=["POST"])
    @rate_limit(max_requests=5, window_seconds=60)
    def image_process():
        ...
"""

from functools import wraps

from flask import jsonify, g, request

from cache import cache


def rate_limit(max_requests: int, window_seconds: int = 60):
    """Limit requests per remote IP within a sliding time window.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Size of the time window in seconds (default 60 s).

    Returns:
        A decorator that wraps a Flask view function.
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or "0.0.0.0"
            endpoint = request.endpoint or request.path
            key = f"rl:{ip}:{endpoint}"

            count = cache.get(key)
            if count is not None and count >= max_requests:
                return (
                    jsonify(
                        {
                            "code": 429,
                            "msg": "Too many requests. Please try again later.",
                            "requestId": getattr(g, "request_id", "-"),
                        }
                    ),
                    429,
                )

            # Increment or initialise the counter.
            cache.set(key, (count or 0) + 1, timeout=window_seconds)
            return f(*args, **kwargs)

        return wrapper

    return decorator
