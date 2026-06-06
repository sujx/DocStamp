"""Flask-Caching SimpleCache initialization.

Provides in-memory caching for:
- /api/stats conversion counts (5-min TTL)
- PDF thumbnail data (avoids re-rendering)
- Duplicate request deduplication
"""

from flask_caching import Cache

cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
})


def init_cache(app):
    """Initialize caching on the Flask application.

    Call during create_app():
        from cache import init_cache
        init_cache(app)
    """
    cache.init_app(app)
