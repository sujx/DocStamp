"""Pydantic v2 request validation schemas.

Enforced through ``@validate_request``: validation failures raise
pydantic.ValidationError → caught by global error_handler → returned as
standardized 422 response.

Multipart endpoints validate their parameters in the service layer instead
(extension whitelist, size caps, magic-number checks).
"""

from pydantic import BaseModel, Field


# ── Markdown ────────────────────────────────────────────────────────────

class MdPreviewSchema(BaseModel):
    """Markdown → HTML preview request."""
    content: str = Field(..., min_length=1, description="Markdown content to preview")


# ── AI endpoints ─────────────────────────────────────────────────────────

class AiTextSchema(BaseModel):
    """Text payload for AI correction / classify / filename endpoints."""
    text: str = Field(..., min_length=1, max_length=8000, description="Input text")


class AiDenoiseSchema(BaseModel):
    """Text payload for AI denoise endpoint (larger limit)."""
    text: str = Field(..., min_length=1, max_length=8000, description="PDF-extracted text to clean")
