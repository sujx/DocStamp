"""Pydantic v2 request validation schemas.

Enforced through ``@validate_request``: validation failures raise
pydantic.ValidationError → caught by global error_handler → returned as
standardized 422 response.

Multipart endpoints validate their parameters in the service layer instead
(extension whitelist, size caps, magic-number checks).
"""

from datetime import date
from typing import Any, cast

from flask_babel import lazy_gettext as _l
from pydantic import BaseModel, ConfigDict, Field, ValidatorFunctionWrapHandler, field_validator, model_validator


# ── Markdown ────────────────────────────────────────────────────────────

class MdPreviewSchema(BaseModel):
    """Markdown → HTML preview request."""
    content: str = Field(..., min_length=1, description="Markdown content to preview")


# ── Meeting minutes ─────────────────────────────────────────────────────

# 表单能提交出的非法输入一律在 DTO 挡住（工单 007）。上限只在这里出现一次，
# 报错文案用 %(limit)s 命名插值带出数字，调上限不必动词条。
MEET_NAME_MAX_CHARS = 50
ROSTER_MAX_COUNT = 100


class MinutesPersonSchema(BaseModel):
    """10.3「标注出席人单位、姓名」的逐人粒度（spec §8 C1）。"""
    org: str = Field("", description="单位")
    name: str = Field("", description="姓名")


class MeetingMinutesSchema(BaseModel):
    """会议纪要生成请求（GB/T 9704-2012 10.3）。字段边界见工单 007。"""

    # pydantic 默认**静默丢弃**未知键，于是前端把 `witness` 拼错就变成
    # 「列席块不排，也不报错」——排版内容无声消失比 422 难查得多。
    model_config = ConfigDict(extra="forbid")

    meet_name: str = Field(..., description="会议名称，与「纪要」拼成纪要标志")
    paragraphs: list[str] = Field(default_factory=list, description="正文自然段")
    attendees: list[MinutesPersonSchema] = Field(default_factory=list, description="出席人员")
    leave: list[MinutesPersonSchema] = Field(default_factory=list, description="请假人员")
    witness: list[MinutesPersonSchema] = Field(default_factory=list, description="列席人员")
    attachments: list[str] = Field(default_factory=list, description="附件名称，按 7.3.4 编排序号")
    cc_orgs: list[str] = Field(default_factory=list, description="抄送机关，按 7.4.2 用顿号相连")
    print_org: str = Field("", description="印发机关，按 7.4.3 左空一字")
    print_date: date | None = Field(None, description="印发日期，按 7.3.5.4 月日不编虚位")

    @field_validator("meet_name")
    @classmethod
    def _clean_meet_name(cls, value: str) -> str:
        """会议名称去首尾空白；全空格等于没填，不能生成「   纪要」。"""
        name = value.strip()
        if not name:
            raise ValueError(_l("Meeting name is required"))
        if len(name) > MEET_NAME_MAX_CHARS:
            raise ValueError(_l("Meeting name is too long (max %(limit)s characters)", limit=MEET_NAME_MAX_CHARS))
        return name

    @field_validator("print_date", mode="wrap")
    @classmethod
    def _read_print_date(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> date | None:
        """日期填错只回一句中文：pydantic 的原文是英文长句，用户看不出该改哪个框。"""
        try:
            return cast("date | None", handler(value))
        except ValueError:
            raise ValueError(_l("Print date must be written as YYYY-MM-DD")) from None

    @model_validator(mode="after")
    def _require_body(self) -> "MeetingMinutesSchema":
        """正文全空行也算没填：10.3 的纪要要素里没有「空正文」这一种。

        名单同理按上限挡——长到四位数的名单只可能是整页误粘贴，
        放过去会把纪要正文冲散成一整页人名。
        """
        if not any(text.strip() for text in self.paragraphs):
            raise ValueError(_l("At least one body paragraph is required"))
        if any(len(items) > ROSTER_MAX_COUNT for items in (self.attendees, self.leave, self.witness)):
            raise ValueError(_l("Too many people in a roster (max %(limit)s)", limit=ROSTER_MAX_COUNT))
        return self
