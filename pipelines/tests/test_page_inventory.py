from pathlib import Path

from madtitan_pipelines.__main__ import main
from madtitan_pipelines.page_inventory import (
    PdfPageInventoryRecord,
    build_page_label_map,
    create_pdf_page_inventory,
    resolve_page_range,
)
from madtitan_pipelines.source_manifest import create_source_book


class FakeRect:
    def __init__(self, width: float = 612.0, height: float = 792.0) -> None:
        self.width = width
        self.height = height


class FakePage:
    def __init__(
        self,
        text: str,
        *,
        images: int = 0,
        width: float = 612.0,
        height: float = 792.0,
        rotation: int = 0,
    ) -> None:
        self.text = text
        self.images = images
        self.rect = FakeRect(width, height)
        self.rotation = rotation

    def get_text(self, _mode: str) -> str:
        return self.text

    def get_images(self, *, full: bool) -> list[object]:
        return [object() for _ in range(self.images)]


class FakeDocument:
    def __init__(self, pages: list[FakePage], labels: list[dict[str, object]] | None = None) -> None:
        self.pages = pages
        self.page_count = len(pages)
        self.labels = labels or []

    def __enter__(self) -> "FakeDocument":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def load_page(self, page_index: int) -> FakePage:
        return self.pages[page_index]

    def get_page_labels(self) -> list[dict[str, object]]:
        return self.labels


def test_create_pdf_page_inventory_enumerates_pages_and_routes_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    source_book = create_source_book(
        book_title="Inventory Book",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
    )
    document = FakeDocument(
        [
            FakePage("This page has a long usable text layer. " * 4),
            FakePage("", images=2),
        ]
    )

    records = create_pdf_page_inventory(source_book, open_pdf=lambda _path: document)

    assert [record.page_number for record in records] == [1, 2]
    assert records[0].page_inventory_id == "inventory-book-p0001-inventory-v1"
    assert records[0].text_layer_status == "usable"
    assert records[0].likely_needs_ocr is False
    assert records[0].recommended_methods == ["pdf_text_layer"]
    assert records[1].text_layer_status == "empty"
    assert records[1].image_count == 2
    assert records[1].likely_needs_ocr is True
    assert records[1].ocr_reasons == [
        "text_layer_empty",
        "image_content_with_poor_text_layer",
    ]
    assert records[1].recommended_methods == ["pdf_text_layer", "local_ocr"]


def test_create_pdf_page_inventory_honors_manifest_page_range(tmp_path: Path) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    source_book = create_source_book(
        book_title="Ranged Book",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
        page_start=2,
        page_end=3,
    )
    document = FakeDocument(
        [
            FakePage("Page one text " * 20),
            FakePage("Page two text " * 20),
            FakePage("Page three text " * 20),
        ]
    )

    records = create_pdf_page_inventory(source_book, open_pdf=lambda _path: document)

    assert [record.page_number for record in records] == [2, 3]


def test_create_pdf_page_inventory_includes_llm_when_preferred_for_poor_text(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    source_book = create_source_book(
        book_title="Vision Book",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
        preferred_methods=["pdf_text_layer", "llm_vision_text"],
        allow_llm_vision=True,
    )
    document = FakeDocument([FakePage("tiny", images=1)])

    records = create_pdf_page_inventory(source_book, open_pdf=lambda _path: document)

    assert records[0].text_layer_status == "low_text"
    assert records[0].recommended_methods == ["pdf_text_layer", "llm_vision_text"]


def test_resolve_page_range_rejects_invalid_ranges() -> None:
    try:
        resolve_page_range(page_count=3, page_start=4, page_end=None)
    except ValueError as error:
        assert "beyond PDF page count" in str(error)
    else:
        raise AssertionError("Expected ValueError")

    try:
        resolve_page_range(page_count=3, page_start=3, page_end=2)
    except ValueError as error:
        assert "after end page" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_build_page_label_map_supports_common_pdf_label_styles() -> None:
    document = FakeDocument(
        [FakePage("x"), FakePage("x"), FakePage("x"), FakePage("x")],
        labels=[
            {"startpage": 0, "style": "r", "firstpagenum": 1},
            {"startpage": 2, "style": "D", "firstpagenum": 1, "prefix": "p."},
        ],
    )

    labels = build_page_label_map(document, page_count=4)

    assert labels == {
        0: "i",
        1: "ii",
        2: "p.1",
        3: "p.2",
    }


def test_cli_page_inventory_inspect_prints_summary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    source_book = create_source_book(
        book_title="Inventory CLI Book",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(source_book.model_dump_json(indent=2) + "\n")

    def fake_create_pdf_page_inventory(_source_book):
        return [
            PdfPageInventoryRecord(
                page_inventory_id="inventory-cli-book-p0001-inventory-v1",
                source_book_id="inventory-cli-book",
                source_file_id=source_book.source_file_id,
                source_file_checksum=source_book.source_file_checksum,
                local_source_ref=source_book.local_source_ref,
                page_number=1,
                page_index=0,
                page_label="1",
                width_points=612,
                height_points=792,
                text_layer_status="empty",
                text_char_count=0,
                image_count=1,
                likely_needs_ocr=True,
                ocr_reasons=["text_layer_empty"],
                preferred_methods=["pdf_text_layer", "local_ocr"],
                recommended_methods=["pdf_text_layer", "local_ocr"],
            )
        ]

    monkeypatch.setattr(
        "madtitan_pipelines.__main__.create_pdf_page_inventory",
        fake_create_pdf_page_inventory,
    )

    result = main(["page-inventory", "inspect", str(manifest_path), "--show-pages"])

    assert result == 0
    output = capsys.readouterr().out
    assert "inventory-cli-book: 1 pages, 1 likely need OCR" in output
    assert "p1 label=1" in output
    assert "1 source book(s), 1 page(s), 1 OCR candidate(s)" in output
