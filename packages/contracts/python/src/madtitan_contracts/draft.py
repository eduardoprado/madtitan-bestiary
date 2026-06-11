from typing import Any

from pydantic import BaseModel, Field


class NormalizationWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class NormalizationMetadata(BaseModel):
    """How a candidate was converted into a structured monster draft."""

    method: str
    normalizer_version: str
    run_id: str
    confidence: float = Field(ge=0, le=1)
    warnings: list[NormalizationWarning] = Field(default_factory=list)


class MonsterOccurrenceDraft(BaseModel):
    """Structured monster payload before it is accepted into the clean dataset."""

    draft_id: str
    candidate_id: str
    normalization: NormalizationMetadata
    monster: dict[str, Any]


class QuarantineError(BaseModel):
    path: str | None = None
    message: str
    code: str


class QuarantineSource(BaseModel):
    source_book_id: str | None = None
    book_title: str | None = None
    ruleset: str | None = None
    source_file_id: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)


class QuarantineRepair(BaseModel):
    eligible_for_manual_review: bool = True
    eligible_for_ocr_retry: bool = False
    eligible_for_llm_repair: bool = False
    next_recommended_step: str = "manual_review"


class QuarantineAudit(BaseModel):
    created_at: str
    parser_version: str
    private_content: bool = True


class QuarantineRecord(BaseModel):
    """Debug record for a candidate or draft that cannot be accepted yet."""

    quarantine_record_id: str
    candidate_id: str | None = None
    draft_id: str | None = None
    reason: str
    severity: str = "review_required"
    source: QuarantineSource = Field(default_factory=QuarantineSource)
    errors: list[QuarantineError] = Field(default_factory=list)
    raw_candidate_ref: str | None = None
    draft_payload: dict[str, Any] = Field(default_factory=dict)
    repair: QuarantineRepair = Field(default_factory=QuarantineRepair)
    audit: QuarantineAudit
