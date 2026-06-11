from dagster import asset


@asset
def page_text(pdf_pages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Layout-aware text extracted from pages with a usable text layer."""
    return []


@asset
def page_ocr_text(pdf_pages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Local OCR output for scanned or low-text pages."""
    return []


@asset
def monster_candidates(
    page_text: list[dict[str, str]],
    page_ocr_text: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Segmented candidate stat blocks with source page spans."""
    return []


@asset
def parsed_monsters(monster_candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    """Structured monster JSON produced by parser rules and heuristics."""
    return []


@asset
def validation_results(parsed_monsters: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    """Accepted, low-confidence, and failed parse records."""
    return {"accepted": [], "quarantined": [], "failed": []}
