"""Global Flask error handlers and request validation decorator.

Provides:
- Standardized JSON error responses for all exception types
- requestId injection and X-Request-Id response header
- @validate_request decorator for Pydantic-based parameter validation

All error responses follow the format:
    {"code": <int>, "msg": "<string>", "requestId": "<uuid>"}
"""

import functools
import uuid
from typing import Type

from flask import Flask, g, jsonify, request
from pydantic import BaseModel, ValidationError

from errors import ErrorCode, ServiceError


# ── requestId Injection ─────────────────────────────────────────────────

def _inject_request_id(app: Flask) -> None:
    """Register before_request hook to generate a per-request requestId."""

    @app.before_request
    def _assign_request_id():
        g.request_id = uuid.uuid4().hex[:12]

    @app.after_request
    def _set_request_id_header(response):
        response.headers["X-Request-Id"] = getattr(g, "request_id", "-")
        return response


# ── Global Error Handlers ───────────────────────────────────────────────

def _format_error(code: int, msg: str, exc_type: str = "") -> tuple:
    """Build a standardized error response tuple."""
    body = {
        "code": code,
        "msg": msg,
        "requestId": getattr(g, "request_id", "-"),
    }
    resp = jsonify(body)
    if exc_type:
        resp.headers["X-Error-Type"] = exc_type
    return resp, code


def register_error_handlers(app: Flask) -> None:
    """Register all Flask error handlers for standardized responses.

    Called during create_app() before route registration.
    """
    _inject_request_id(app)

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(e: ValidationError):
        """Pydantic validation failure → 422."""
        errors = e.errors()
        first_message = errors[0]["msg"] if errors else "Validation failed"
        return _format_error(422, first_message, "ValidationError")

    @app.errorhandler(ServiceError)
    def handle_service_error(e: ServiceError):
        """Business logic error → status from exception."""
        return _format_error(e.status, e.message, "ServiceError")

    @app.errorhandler(ValueError)
    def handle_value_error(e: ValueError):
        """ValueError from services → 400."""
        return _format_error(400, str(e))

    @app.errorhandler(404)
    def handle_not_found(e):
        return _format_error(404, "Resource not found")

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return _format_error(405, "Method not allowed")

    @app.errorhandler(413)
    def handle_request_too_large(e):
        return _format_error(413, "Request entity too large")

    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception):
        """Catch-all for unhandled exceptions."""
        is_debug = app.config.get("DEBUG", False)
        msg = str(e) if is_debug else "系统异常"
        app.logger.exception("Unhandled exception: %s", e)
        return _format_error(500, msg, e.__class__.__name__)


# ── Request Validation Decorator ────────────────────────────────────────

def validate_request(
    body: Type[BaseModel] | None = None,
    form: Type[BaseModel] | None = None,
    query: Type[BaseModel] | None = None,
):
    """Decorator: validate Flask request data with Pydantic schemas.

    Usage:
        @app.route("/api/convert", methods=["POST"])
        @validate_request(body=MdConvertSchema)
        def md_convert(body: MdConvertSchema):
            ...

    The validated model is injected as a keyword argument matching the
    parameter name ('body', 'form', or 'query').

    On validation failure, raises pydantic.ValidationError which is
    caught by the global handler → 422 response.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if body is not None:
                data = request.get_json(silent=True)
                if data is None:
                    raise ServiceError(
                        ErrorCode.VALIDATION_ERROR,
                        "Request body must be valid JSON",
                        status=422,
                    )
                validated = body.model_validate(data)
                kwargs["body"] = validated

            if form is not None:
                # Merge request.form + request.files for file-aware validation
                form_data = dict(request.form)
                validated = form.model_validate(form_data)
                kwargs["form"] = validated

            if query is not None:
                query_data = dict(request.args)
                validated = query.model_validate(query_data)
                kwargs["query"] = validated

            return func(*args, **kwargs)

        return wrapper

    return decorator
