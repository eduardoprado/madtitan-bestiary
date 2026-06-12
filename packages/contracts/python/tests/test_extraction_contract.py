from pathlib import Path

import pytest
from pydantic import ValidationError

from madtitan_contracts.extraction import ExtractedPageText, PageContentAnnotation, SourceBook


def test_source_book_fixture_validates_user_provided_metadata() -> None:
    path = Path(__file__).parents[4] / "samples/source_books/monster_manual_2024_source.json"

    source_book = SourceBook.model_validate_json(path.read_text())

    assert source_book.book_title == "Monster Manual 2024"
    assert source_book.ruleset == "DND 5.5e"
    assert source_book.extraction_settings.allow_llm_vision is True
    assert source_book.extraction_settings.preferred_methods == [
        "pdf_text_layer",
        "local_ocr",
        "llm_vision_text",
    ]


def test_extracted_page_text_fixture_accepts_text_ref() -> None:
    path = (
        Path(__file__).parents[4]
        / "samples/extracted_text/srd/non_monster_page_pdf_text_layer.json"
    )

    extracted = ExtractedPageText.model_validate_json(path.read_text())

    assert extracted.source.page_number == 12
    assert extracted.extraction.method == "pdf_text_layer"
    assert extracted.text is None
    assert extracted.text_ref == "private://extracted-text/mm2024/p0012/pdf-text-v1.txt"
    assert extracted.layout.blocks[0].reading_order == 0


def test_extracted_page_text_fixture_accepts_inline_redacted_text() -> None:
    path = Path(__file__).parents[4] / "samples/extracted_text/srd/dire_wolf_pdf_text_layer.json"

    extracted = ExtractedPageText.model_validate_json(path.read_text())

    assert extracted.extraction.status == "succeeded"
    assert extracted.text == "[redacted fixture text: one monster statblock page detected]"
    assert extracted.layout.blocks[0].bbox is not None
    assert extracted.layout.blocks[0].bbox.page == 352


def test_failed_extraction_fixture_can_omit_text_when_warning_is_present() -> None:
    path = Path(__file__).parents[4] / "samples/extracted_text/srd/failed_ocr_page.json"

    extracted = ExtractedPageText.model_validate_json(path.read_text())

    assert extracted.extraction.status == "failed"
    assert extracted.text is None
    assert extracted.text_ref is None
    assert extracted.extraction.warnings[0].code == "no_readable_text"


def test_successful_extraction_requires_text_or_text_ref() -> None:
    path = Path(__file__).parents[4] / "samples/extracted_text/srd/dire_wolf_pdf_text_layer.json"
    payload = ExtractedPageText.model_validate_json(path.read_text()).model_dump(mode="json")
    payload.pop("text")
    payload["text_ref"] = None

    with pytest.raises(ValidationError, match="requires either text or text_ref"):
        ExtractedPageText.model_validate(payload)


def test_failed_extraction_requires_warning() -> None:
    path = Path(__file__).parents[4] / "samples/extracted_text/srd/failed_ocr_page.json"
    payload = ExtractedPageText.model_validate_json(path.read_text()).model_dump(mode="json")
    payload["extraction"]["warnings"] = []

    with pytest.raises(ValidationError, match="Failed extraction requires at least one warning"):
        ExtractedPageText.model_validate(payload)


def test_page_content_annotation_fixture_validates_image_and_lore_detections() -> None:
    path = (
        Path(__file__).parents[4]
        / "samples/annotations/srd/adult_red_dragon_llm_vision_annotation.json"
    )

    annotation = PageContentAnnotation.model_validate_json(path.read_text())

    assert annotation.method == "llm_vision_annotation"
    assert {detection.kind for detection in annotation.detections} == {
        "monster_image",
        "monster_lore",
    }
    image = next(detection for detection in annotation.detections if detection.kind == "monster_image")
    lore = next(detection for detection in annotation.detections if detection.kind == "monster_lore")
    assert image.monster_name_hint == "Adult Red Dragon"
    assert image.bbox is not None
    assert lore.text_ref == "private://monster-lore/mm2024/adult-red-dragon/p0255/lore-v1.txt"
    assert lore.text_hash == "sha256:mm2024-adult-red-dragon-lore-private-v1"
    assert lore.text_span_ref is not None
    assert lore.block_ids == ["mm2024-p0255-b-lore"]
