"""Pydantic v2 request validation schemas.

Every API endpoint has a corresponding Schema class that validates
incoming request data before it reaches the service layer.

Validation failures raise pydantic.ValidationError → caught by
global error_handler → returned as standardized 422 response.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ── MD Conversion ───────────────────────────────────────────────────────

class MdConvertSchema(BaseModel):
    """Markdown content → DOCX conversion request."""
    content: str = Field(..., min_length=1, description="Markdown content to convert")


class MdPreviewSchema(BaseModel):
    """Markdown → HTML preview request."""
    content: str = Field(..., min_length=1, description="Markdown content to preview")


# ── Properties ──────────────────────────────────────────────────────────

class PropertiesModifySchema(BaseModel):
    """Office document property modification request."""
    created: Optional[str] = Field(None, description="ISO-8601 creation timestamp")
    modified: Optional[str] = Field(None, description="ISO-8601 modification timestamp")
    creator: Optional[str] = Field(None, max_length=255, description="Author name")
    last_modified_by: Optional[str] = Field(None, max_length=255, description="Last modifier name")
    unify_time: bool = Field(False, description="Set created and modified to same value")
    unified_time: Optional[str] = Field(None, description="Single timestamp for unified mode")

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        """At least one property must be provided."""
        if not any([self.created, self.modified, self.creator,
                    self.last_modified_by, self.unified_time]):
            raise ValueError("At least one property to modify is required")
        return self


# ── Image to PDF ────────────────────────────────────────────────────────

class Img2PdfSchema(BaseModel):
    """Image merge → PDF request."""
    page_size: str = Field("original", description="Page size preset")
    filename: str = Field("merged.pdf", max_length=255, description="Output filename")
    order: Optional[list[int]] = Field(None, description="Image sort order array")

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: str) -> str:
        allowed = {"original", "a4", "a4_landscape", "letter", "letter_landscape"}
        if v not in allowed:
            raise ValueError(f"page_size must be one of: {', '.join(sorted(allowed))}")
        return v


# ── PDF to Images ───────────────────────────────────────────────────────

class Pdf2ImgSchema(BaseModel):
    """PDF → images request."""
    format: str = Field("png", description="Output image format")
    dpi: int = Field(200, ge=72, le=600, description="Output resolution in DPI")
    pages: Optional[list[int]] = Field(None, description="Pages to convert (1-indexed)")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in ("png", "jpeg"):
            raise ValueError("format must be 'png' or 'jpeg'")
        return v


# ── Print Split ─────────────────────────────────────────────────────────

class PrintSplitSchema(BaseModel):
    """PDF print split request."""
    batch_size: int = Field(..., ge=1, le=1000, description="Pages per batch")
    interval: int = Field(0, ge=0, le=86400, description="Interval seconds between batches")


# ── Watermark ───────────────────────────────────────────────────────────

class WatermarkAddSchema(BaseModel):
    """Watermark addition request."""
    watermark_type: str = Field("text", description="Watermark type: text or image")
    text: str = Field("", max_length=500, description="Watermark text content")
    font: str = Field("Helvetica", max_length=100, description="Font name")
    font_size: int = Field(48, ge=1, le=500, description="Font size in points")
    color: str = Field("#D0D0D0", max_length=9, description="Hex color value")
    opacity: float = Field(0.3, ge=0.0, le=1.0, description="Opacity 0.0–1.0")
    rotation: float = Field(-45.0, ge=-360.0, le=360.0, description="Rotation degrees")
    position: str = Field("tile", description="Placement: tile or center")
    spacing_x: int = Field(200, ge=0, le=2000, description="Horizontal spacing (pt)")
    spacing_y: int = Field(200, ge=0, le=2000, description="Vertical spacing (pt)")
    image_size: Optional[int] = Field(None, ge=1, le=1000, description="Image watermark size (pt)")

    @field_validator("watermark_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("text", "image"):
            raise ValueError("watermark_type must be 'text' or 'image'")
        return v

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        if v not in ("tile", "center"):
            raise ValueError("position must be 'tile' or 'center'")
        return v


# ── PDF Editor ──────────────────────────────────────────────────────────

class PdfDeleteSchema(BaseModel):
    """PDF page deletion request."""
    pages: list[int] = Field(..., min_length=1, description="Page numbers to delete (1-indexed)")


class PdfInsertSchema(BaseModel):
    """PDF page insertion request."""
    at_position: int = Field(0, ge=0, description="Insert after page N (0 = beginning)")
    insert_pages: Optional[list[int]] = Field(None, description="Pages to insert from source")


class PdfReorderSchema(BaseModel):
    """PDF page reorder request."""
    order: list[int] = Field(..., min_length=1, description="New page order (1-indexed)")


# ── Excel Merge ─────────────────────────────────────────────────────────

class ExcelMergeSchema(BaseModel):
    """Excel/CSV merge request."""
    filename: str = Field("merged.xlsx", max_length=255, description="Output filename")


# ── Common / Pagination ─────────────────────────────────────────────────

class PaginationSchema(BaseModel):
    """Common pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Items per page")


class TaskPollSchema(BaseModel):
    """Task status polling parameters."""
    task_id: str = Field(..., min_length=1, max_length=64, description="Celery task UUID")
