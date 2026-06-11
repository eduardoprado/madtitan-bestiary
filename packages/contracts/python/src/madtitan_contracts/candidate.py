from typing import Literal

from pydantic import BaseModel, Field


CandidateStatus = Literal["pending", "accepted", "quarantined", "superseded", "ignored"]


class CandidateSource(BaseModel):
    """Book, file, and page identity for a candidate segment."""

    source_book_id: str
    book_title: str
    ruleset: str
    source_file_id: str
    source_file_checksum: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    page_labels: list[str] = Field(default_factory=list)


class SourceFormatProfile(BaseModel):
    """Source-specific stat-block conventions observed for this candidate."""

    profile_id: str | None = None
    profile_version: str | None = None
    statblock_family: str | None = None
    layout_type: str | None = None
    expected_single_page: bool | None = None
    column_count: int | None = Field(default=None, ge=1)
    section_order: list[str] = Field(default_factory=list)
    heading_patterns: list[str] = Field(default_factory=list)
    known_variations: list[str] = Field(default_factory=list)
    notes: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class CandidateLineage(BaseModel):
    """How this candidate was created and what earlier records it came from."""

    extracted_page_text_ids: list[str] = Field(default_factory=list)
    extraction_methods: list[str] = Field(default_factory=list)
    segmentation_run_id: str
    segmentation_method: str
    segmenter_version: str
    parent_candidate_id: str | None = None
    repair_source_quarantine_record_id: str | None = None


class CandidateSection(BaseModel):
    label: str
    text: str


class CandidatePayload(BaseModel):
    """The private candidate text plus best-effort hints from segmentation."""

    name_hint: str | None = None
    creature_type_hint: str | None = None
    page_span_text: str | None = None
    page_span_text_ref: str | None = None
    sections: list[CandidateSection] = Field(default_factory=list)
    start_marker: str | None = None
    end_marker: str | None = None
    raw_text_hash: str | None = None


class CandidateBoundingBox(BaseModel):
    page: int = Field(ge=1)
    x0: float
    y0: float
    x1: float
    y1: float
    unit: str = "page_ratio"


class CandidateLocation(BaseModel):
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    text_start_offset: int | None = Field(default=None, ge=0)
    text_end_offset: int | None = Field(default=None, ge=0)
    bounding_boxes: list[CandidateBoundingBox] = Field(default_factory=list)


class CandidateWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class CandidateQuality(BaseModel):
    confidence: float = Field(ge=0, le=1)
    text_quality: str
    segmentation_quality: str
    warnings: list[CandidateWarning] = Field(default_factory=list)


class CandidateNormalizationState(BaseModel):
    recommended_method: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    last_attempt_at: str | None = None


class CandidateAudit(BaseModel):
    created_at: str
    created_by: str
    private_content: bool = True
    updated_at: str | None = None


class MonsterCandidate(BaseModel):
    """A segmented, not-yet-normalized monster-like stat block candidate."""

    candidate_id: str
    status: CandidateStatus = "pending"
    source: CandidateSource
    source_format: SourceFormatProfile = Field(default_factory=SourceFormatProfile)
    lineage: CandidateLineage
    candidate: CandidatePayload
    location: CandidateLocation
    quality: CandidateQuality
    normalization: CandidateNormalizationState = Field(default_factory=CandidateNormalizationState)
    audit: CandidateAudit
