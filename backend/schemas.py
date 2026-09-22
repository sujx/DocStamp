"""Pydantic v2 request validation schemas.

Enforced through ``@validate_request``: validation failures raise
pydantic.ValidationError → caught by global error_handler → returned as
standardized 422 response.

Multipart endpoints validate their parameters in the service layer instead
(extension whitelist, size caps, magic-number checks).
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


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


# ── Company Lookup ───────────────────────────────────────────────────────

class CompanyLookupSchema(BaseModel):
    """Single company name → website lookup request."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name to look up")


class CompanyBatchLookupSchema(BaseModel):
    """Batch company name → website lookup request."""
    names: list[str] = Field(..., min_length=1, max_length=100, description="Company names to look up")


class CompanyConfirmSchema(BaseModel):
    """Confirm and save a company lookup result to local database."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    website: str = Field(..., min_length=1, max_length=500, description="Website URL")
    corrected_name: Optional[str] = Field(None, max_length=200, description="User-corrected company name")
    corrected_website: Optional[str] = Field(None, max_length=500, description="User-corrected website URL")

    @field_validator("website")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if "://" not in v:
            raise ValueError("Website must include scheme (https://...)")
        return v
