from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal

from madtitan_contracts.extraction import ExtractionMethod, SourceBook
from pydantic import BaseModel, Field


TextLayerStatus = Literal["usable", "low_text", "empty", "unavailable"]
PageInventoryOpenPdf = Callable[[Path], Any]

MIN_USABLE_TEXT_CHARS = 80


class PdfPageInventoryRecord(BaseModel):
    """Internal per-page routing record created before extraction attempts."""

    page_inventory_id: str
    source_book_id: str
    source_file_id: str
    source_file_checksum: str
    local_source_ref: str
    page_number: int = Field(ge=1)
    page_index: int = Field(ge=0)
    page_label: str | None = None
    width_points: float = Field(gt=0)
    height_points: float = Field(gt=0)
    rotation: int = 0
    text_layer_status: TextLayerStatus
    text_char_count: int = Field(ge=0)
    image_count: int = Field(ge=0)
    likely_needs_ocr: bool
    ocr_reasons: list[str] = Field(default_factory=list)
    preferred_methods: list[ExtractionMethod] = Field(default_factory=list)
    recommended_methods: list[ExtractionMethod] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def create_pdf_page_inventory(
    source_book: SourceBook,
    *,
    open_pdf: PageInventoryOpenPdf | None = None,
    min_usable_text_chars: int = MIN_USABLE_TEXT_CHARS,
) -> list[PdfPageInventoryRecord]:
    """Enumerate a source PDF and create internal page inventory records."""

    pdf_path = Path(source_book.local_source_ref).expanduser()
    opener = open_pdf or open_pymupdf_document
    with opener(pdf_path) as document:
        page_count = int(document.page_count)
        page_start, page_end = resolve_page_range(
            page_count=page_count,
            page_start=source_book.extraction_settings.page_start,
            page_end=source_book.extraction_settings.page_end,
        )
        page_labels = build_page_label_map(document, page_count)
        records = []
        for page_number in range(page_start, page_end + 1):
            page_index = page_number - 1
            page = document.load_page(page_index)
            records.append(
                create_page_inventory_record(
                    source_book=source_book,
                    page=page,
                    page_number=page_number,
                    page_index=page_index,
                    page_label=page_labels.get(page_index),
                    min_usable_text_chars=min_usable_text_chars,
                )
            )
    return records


def create_page_inventory_record(
    *,
    source_book: SourceBook,
    page: Any,
    page_number: int,
    page_index: int,
    page_label: str | None,
    min_usable_text_chars: int,
) -> PdfPageInventoryRecord:
    text_layer_status, text_char_count, text_error = inspect_text_layer(
        page,
        min_usable_text_chars=min_usable_text_chars,
    )
    image_count = inspect_image_count(page)
    likely_needs_ocr, ocr_reasons = classify_ocr_need(
        text_layer_status=text_layer_status,
        image_count=image_count,
    )
    preferred_methods = list(source_book.extraction_settings.preferred_methods)
    recommended_methods = recommend_methods(
        preferred_methods=preferred_methods,
        text_layer_status=text_layer_status,
        likely_needs_ocr=likely_needs_ocr,
    )
    rect = page.rect

    metadata: dict[str, Any] = {}
    if text_error:
        metadata["text_layer_error"] = text_error

    return PdfPageInventoryRecord(
        page_inventory_id=f"{source_book.source_book_id}-p{page_number:04d}-inventory-v1",
        source_book_id=source_book.source_book_id,
        source_file_id=source_book.source_file_id,
        source_file_checksum=source_book.source_file_checksum,
        local_source_ref=source_book.local_source_ref,
        page_number=page_number,
        page_index=page_index,
        page_label=page_label,
        width_points=float(rect.width),
        height_points=float(rect.height),
        rotation=int(getattr(page, "rotation", 0) or 0),
        text_layer_status=text_layer_status,
        text_char_count=text_char_count,
        image_count=image_count,
        likely_needs_ocr=likely_needs_ocr,
        ocr_reasons=ocr_reasons,
        preferred_methods=preferred_methods,
        recommended_methods=recommended_methods,
        metadata=metadata,
    )


def inspect_text_layer(
    page: Any,
    *,
    min_usable_text_chars: int,
) -> tuple[TextLayerStatus, int, str | None]:
    try:
        text = page.get_text("text")
    except Exception as error:  # pragma: no cover - depends on PDF parser internals.
        return "unavailable", 0, str(error)

    text_char_count = len((text or "").strip())
    if text_char_count == 0:
        return "empty", 0, None
    if text_char_count < min_usable_text_chars:
        return "low_text", text_char_count, None
    return "usable", text_char_count, None


def inspect_image_count(page: Any) -> int:
    try:
        return len(page.get_images(full=True))
    except Exception:  # pragma: no cover - depends on PDF parser internals.
        return 0


def classify_ocr_need(
    *,
    text_layer_status: TextLayerStatus,
    image_count: int,
) -> tuple[bool, list[str]]:
    reasons = []
    if text_layer_status in {"empty", "unavailable"}:
        reasons.append(f"text_layer_{text_layer_status}")
    if text_layer_status == "low_text":
        reasons.append("text_layer_low_text")
    if image_count > 0 and text_layer_status in {"empty", "low_text", "unavailable"}:
        reasons.append("image_content_with_poor_text_layer")
    return bool(reasons), reasons


def recommend_methods(
    *,
    preferred_methods: list[ExtractionMethod],
    text_layer_status: TextLayerStatus,
    likely_needs_ocr: bool,
) -> list[ExtractionMethod]:
    recommended_methods = []
    if "pdf_text_layer" in preferred_methods and text_layer_status != "unavailable":
        recommended_methods.append("pdf_text_layer")
    if likely_needs_ocr and "local_ocr" in preferred_methods:
        recommended_methods.append("local_ocr")
    if likely_needs_ocr and "llm_vision_text" in preferred_methods:
        recommended_methods.append("llm_vision_text")
    if not recommended_methods:
        return list(preferred_methods)
    return recommended_methods


def resolve_page_range(
    *,
    page_count: int,
    page_start: int | None,
    page_end: int | None,
) -> tuple[int, int]:
    if page_count < 1:
        raise ValueError("PDF has no pages.")

    resolved_start = page_start or 1
    resolved_end = page_end or page_count
    if resolved_start > page_count:
        raise ValueError(
            f"Invalid page range: start page {resolved_start} is beyond PDF page count {page_count}."
        )
    if resolved_end > page_count:
        raise ValueError(
            f"Invalid page range: end page {resolved_end} is beyond PDF page count {page_count}."
        )
    if resolved_start > resolved_end:
        raise ValueError(
            f"Invalid page range: start page {resolved_start} is after end page {resolved_end}."
        )
    return resolved_start, resolved_end


def build_page_label_map(document: Any, page_count: int) -> dict[int, str]:
    try:
        label_rules = document.get_page_labels()
    except Exception:
        return {index: str(index + 1) for index in range(page_count)}

    if not label_rules:
        return {index: str(index + 1) for index in range(page_count)}

    labels = {}
    rules = sorted(label_rules, key=lambda rule: int(rule.get("startpage", 0)))
    for rule_index, rule in enumerate(rules):
        start_index = int(rule.get("startpage", 0))
        next_start = (
            int(rules[rule_index + 1].get("startpage", page_count))
            if rule_index + 1 < len(rules)
            else page_count
        )
        for page_index in range(start_index, next_start):
            labels[page_index] = format_page_label(rule, page_index - start_index)

    return {index: labels.get(index, str(index + 1)) for index in range(page_count)}


def format_page_label(rule: dict[str, Any], offset: int) -> str:
    prefix = str(rule.get("prefix") or "")
    first_page_number = int(rule.get("firstpagenum") or 1)
    value = first_page_number + offset
    style = rule.get("style") or "D"
    if style == "D":
        return f"{prefix}{value}"
    if style == "r":
        return f"{prefix}{to_roman(value).lower()}"
    if style == "R":
        return f"{prefix}{to_roman(value)}"
    if style == "a":
        return f"{prefix}{to_alpha(value).lower()}"
    if style == "A":
        return f"{prefix}{to_alpha(value)}"
    return f"{prefix}{value}"


def to_roman(value: int) -> str:
    numerals = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result = []
    remaining = value
    for number, numeral in numerals:
        while remaining >= number:
            result.append(numeral)
            remaining -= number
    return "".join(result)


def to_alpha(value: int) -> str:
    result = []
    remaining = value
    while remaining > 0:
        remaining -= 1
        result.append(chr(ord("A") + (remaining % 26)))
        remaining //= 26
    return "".join(reversed(result))


def open_pymupdf_document(path: Path) -> Any:
    try:
        import fitz
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "PyMuPDF is required for PDF page inventory. Run this command through "
            "`uv run madtitan-pipelines ...` so pipeline dependencies are available."
        ) from error
    return fitz.open(path)
