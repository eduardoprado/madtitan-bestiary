from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


ExtractionMethod = Literal[
    "pdf_text_layer",
    "local_ocr",
    "llm_vision_text",
    "manual_transcription",
]

ExtractionStatus = Literal["succeeded", "partial", "failed"]
AnnotationMethod = Literal["llm_vision_annotation", "manual_review", "heuristic_layout"]
DetectionKind = Literal["monster_image", "monster_lore"]


class ExtractionWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class ExtractionSettings(BaseModel):
    """Book-level extraction preferences supplied by the user or manifest."""

    preferred_methods: list[ExtractionMethod] = Field(default_factory=list)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    render_dpi: int | None = Field(default=None, ge=1)
    allow_llm_vision: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceBook(BaseModel):
    """User-provided manifest row for a private source PDF/book."""

    source_book_id: str
    book_title: str
    ruleset: str
    source_file_id: str
    source_file_checksum: str
    local_source_ref: str | None = None
    private_source: bool = True
    extraction_settings: ExtractionSettings = Field(default_factory=ExtractionSettings)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedPageSource(BaseModel):
    """Source book and page identity inherited from the source manifest."""

    source_book_id: str
    book_title: str
    ruleset: str
    source_file_id: str
    source_file_checksum: str
    page_number: int = Field(ge=1)
    page_label: str | None = None


class TextExtractionMetadata(BaseModel):
    method: ExtractionMethod
    status: ExtractionStatus
    tool_name: str
    tool_version: str | None = None
    run_id: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    quality: str | None = None
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PageBoundingBox(BaseModel):
    page: int = Field(ge=1)
    x0: float
    y0: float
    x1: float
    y1: float
    unit: str = "page_ratio"


class PageTextBlock(BaseModel):
    block_id: str
    text: str | None = None
    text_ref: str | None = None
    bbox: PageBoundingBox | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reading_order: int = Field(ge=0)

    @model_validator(mode="after")
    def require_text_or_ref(self) -> "PageTextBlock":
        if self.text is None and self.text_ref is None:
            raise ValueError("Page text block requires either text or text_ref")
        return self


class PageLayout(BaseModel):
    has_text_layer: bool
    is_scanned: bool
    page_width: float | None = Field(default=None, ge=0)
    page_height: float | None = Field(default=None, ge=0)
    page_unit: str = "pt"
    blocks: list[PageTextBlock] = Field(default_factory=list)


class ExtractedPageText(BaseModel):
    """One page-level text extraction attempt from a source PDF/book."""

    extracted_page_text_id: str
    source: ExtractedPageSource
    extraction: TextExtractionMetadata
    text: str | None = None
    text_ref: str | None = None
    text_hash: str | None = None
    layout: PageLayout
    created_at: str

    @model_validator(mode="after")
    def validate_text_presence(self) -> "ExtractedPageText":
        if self.extraction.status != "failed" and self.text is None and self.text_ref is None:
            raise ValueError("Successful or partial extraction requires either text or text_ref")
        if self.extraction.status == "failed" and not self.extraction.warnings:
            raise ValueError("Failed extraction requires at least one warning")
        return self


class PageContentDetection(BaseModel):
    kind: DetectionKind
    monster_name_hint: str | None = None
    bbox: PageBoundingBox | None = None
    text_span_ref: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PageContentAnnotation(BaseModel):
    """Page-level monster image/lore ownership hints from vision or review."""

    annotation_id: str
    extracted_page_text_id: str
    source_book_id: str
    page_number: int = Field(ge=1)
    method: AnnotationMethod
    run_id: str
    confidence: float = Field(ge=0, le=1)
    detections: list[PageContentDetection] = Field(default_factory=list)
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)
