"""Error code enumeration, structured service results, and business exception.

Provides the foundation for the Service Layer DTO pattern:
- ErrorCode: Categorized error codes for all business operations
- ServiceResult: Standard return type wrapping success/failure + typed data
- ServiceError: Exception caught by global handler for automatic JSON responses
"""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


# ── Error Code Enumeration ─────────────────────────────────────────────

class ErrorCode(Enum):
    """Business error codes, one per known failure mode."""

    # Common
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    MAGIC_NUMBER_MISMATCH = "MAGIC_NUMBER_MISMATCH"

    # PDF operations
    PDF_READ_ERROR = "PDF_READ_ERROR"
    PDF_EMPTY = "PDF_EMPTY"
    PDF_PAGE_OUT_OF_RANGE = "PDF_PAGE_OUT_OF_RANGE"
    PDF_NO_PAGES_SPECIFIED = "PDF_NO_PAGES_SPECIFIED"

    # Watermark
    WATERMARK_TEXT_REQUIRED = "WATERMARK_TEXT_REQUIRED"
    WATERMARK_IMAGE_REQUIRED = "WATERMARK_IMAGE_REQUIRED"

    # Excel
    EXCEL_STRUCTURE_MISMATCH = "EXCEL_STRUCTURE_MISMATCH"
    EXCEL_INSUFFICIENT_FILES = "EXCEL_INSUFFICIENT_FILES"

    # Conversion
    CONVERSION_FAILED = "CONVERSION_FAILED"
    CONVERSION_RETRY_EXHAUSTED = "CONVERSION_RETRY_EXHAUSTED"
    TOOL_NOT_AVAILABLE = "TOOL_NOT_AVAILABLE"

    # Async tasks
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_FAILED = "TASK_FAILED"

    # Company lookup
    LOOKUP_NOT_FOUND = "LOOKUP_NOT_FOUND"
    LOOKUP_FAILED = "LOOKUP_FAILED"
    LOOKUP_ALREADY_EXISTS = "LOOKUP_ALREADY_EXISTS"

    # Internal
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ── Structured Service Result ───────────────────────────────────────────

@dataclass
class ServiceResult(Generic[T]):
    """Standard return type for ALL service functions.

    Forces callers to explicitly handle success/failure paths.

    Usage:
        def my_service(path: str) -> ServiceResult[dict]:
            try:
                data = do_work(path)
                return ServiceResult.ok(data)
            except ValueError as e:
                return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, str(e))
    """

    success: bool
    data: T | None = None
    error: ErrorCode | None = None
    message: str = ""

    @staticmethod
    def ok(data: T) -> "ServiceResult[T]":
        """Create a successful result with typed data."""
        return ServiceResult(success=True, data=data)

    @staticmethod
    def fail(error: ErrorCode, message: str = "") -> "ServiceResult":
        """Create a failure result with error code and message."""
        return ServiceResult(success=False, error=error, message=message)


# ── Business Exception ──────────────────────────────────────────────────

class ServiceError(Exception):
    """Business exception caught by global Flask error handler.

    Automatically converted to standardized JSON response:
        {"code": <status>, "msg": <message>, "requestId": "..."}

    Attributes:
        code: ErrorCode enum value
        message: Human-readable description
        status: HTTP status code (default 400)
    """

    def __init__(self, code: ErrorCode, message: str = "", status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)
