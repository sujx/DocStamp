"""Retry decorator for document processing operations.

Applies exponential backoff retry to functions that depend on external
tools (Pandoc, LibreOffice, pdftoppm) which may transiently fail.

After max_retries, degrades gracefully to a ServiceResult.fail() instead
of raising, giving the user a clear error message.
"""

import functools
import logging
import time

from errors import ErrorCode, ServiceResult

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_retries: int = 2,
    backoff: float = 1.0,
    degrade_message: str = "文件格式错误，请检查文件完整性",
):
    """Decorator: retry a function on any exception, degrade on exhaustion.

    Retry strategy:
        Attempt 0: immediate
        Attempt 1: wait backoff * 1 seconds
        Attempt 2: wait backoff * 2 seconds
        Exhausted: return ServiceResult.fail(CONVERSION_RETRY_EXHAUSTED)

    Args:
        max_retries: Number of retry attempts (total calls = max_retries + 1).
        backoff: Base backoff multiplier in seconds.
        degrade_message: User-facing message when all retries are exhausted.

    Usage:
        @retry_on_failure(max_retries=2)
        def convert_pdf(path, output):
            subprocess.run(["pandoc", path, "-o", output], check=True)
            return ServiceResult.ok(output)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = backoff * (2 ** attempt)
                        logger.warning(
                            "Retry %d/%d for %s (%.1fs delay): %s",
                            attempt + 1, max_retries, func.__name__, delay, e,
                        )
                        time.sleep(delay)

            logger.error(
                "%s failed after %d retries: %s",
                func.__name__, max_retries, last_error,
            )
            return ServiceResult.fail(
                ErrorCode.CONVERSION_RETRY_EXHAUSTED,
                degrade_message,
            )

        return wrapper

    return decorator
