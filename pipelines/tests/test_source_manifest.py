import hashlib
import json
from pathlib import Path

from madtitan_contracts.extraction import SourceBook
from madtitan_pipelines.__main__ import main
from madtitan_pipelines.source_manifest import (
    SourceFileNotFoundError,
    create_source_book,
    load_source_manifest,
    load_source_manifests,
    slugify,
    write_source_manifest,
)


def test_slugify_creates_source_book_id() -> None:
    assert slugify("Monster Manual 2024") == "monster-manual-2024"
    assert slugify(" Flee, Mortals! ") == "flee-mortals"


def test_create_source_book_computes_checksum_and_file_id(tmp_path: Path) -> None:
    pdf_path = tmp_path / "Monster Manual 2024.pdf"
    pdf_bytes = b"%PDF fixture content"
    pdf_path.write_bytes(pdf_bytes)

    source_book = create_source_book(
        book_title="Monster Manual 2024",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
        page_start=1,
        page_end=384,
        render_dpi=220,
        allow_llm_vision=True,
    )

    expected_checksum = f"sha256:{hashlib.sha256(pdf_bytes).hexdigest()}"
    assert source_book.source_book_id == "monster-manual-2024"
    assert source_book.book_title == "Monster Manual 2024"
    assert source_book.ruleset == "DND 5.5e"
    assert source_book.source_file_checksum == expected_checksum
    assert source_book.source_file_id.startswith("monster-manual-2024-")
    assert source_book.extraction_settings.page_start == 1
    assert source_book.extraction_settings.page_end == 384
    assert source_book.extraction_settings.allow_llm_vision is True


def test_write_and_load_source_manifest(tmp_path: Path) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    source_book = create_source_book(
        book_title="Synthetic Bestiary",
        ruleset="DND 5.5e",
        local_source_ref=str(pdf_path),
    )

    manifest_path = write_source_manifest(source_book, tmp_path / "manifests")

    loaded = load_source_manifest(manifest_path)
    assert loaded == source_book
    assert SourceBook.model_validate_json(manifest_path.read_text()).source_book_id == (
        "synthetic-bestiary"
    )


def test_create_source_book_reports_missing_source_file(tmp_path: Path) -> None:
    missing_pdf_path = tmp_path / "missing.pdf"

    try:
        create_source_book(
            book_title="Missing Book",
            ruleset="DND 5.5e",
            local_source_ref=str(missing_pdf_path),
        )
    except SourceFileNotFoundError as error:
        assert "Source PDF file was not located" in str(error)
        assert "Please add the file or correct the path and try again" in str(error)
    else:
        raise AssertionError("Expected SourceFileNotFoundError")


def test_load_source_manifests_from_directory(tmp_path: Path) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    manifest_dir = tmp_path / "manifests"
    write_source_manifest(
        create_source_book(
            book_title="Book A",
            ruleset="DND 5.5e",
            local_source_ref=str(pdf_path),
            source_book_id="book-a",
        ),
        manifest_dir,
    )
    write_source_manifest(
        create_source_book(
            book_title="Book B",
            ruleset="DND 5e",
            local_source_ref=str(pdf_path),
            source_book_id="book-b",
        ),
        manifest_dir,
    )

    loaded = load_source_manifests(manifest_dir)

    assert [manifest.source_book_id for manifest in loaded] == ["book-a", "book-b"]


def test_cli_validate_manifest(tmp_path: Path, capsys) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    manifest_path = write_source_manifest(
        create_source_book(
            book_title="CLI Validate Book",
            ruleset="DND 5.5e",
            local_source_ref=str(pdf_path),
        ),
        tmp_path,
    )

    result = main(["source-manifest", "validate", str(manifest_path)])

    assert result == 0
    assert "1 accepted, 0 failed" in capsys.readouterr().out


def test_cli_create_manifest_interactive(tmp_path: Path, monkeypatch, capsys) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    answers = iter(
        [
            "y",
            "Interactive Book",
            "DND 5.5e",
            str(pdf_path),
            "",
            "",
            "",
            "",
            "",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    result = main(["source-manifest", "create", "--output-dir", str(tmp_path / "manifests")])

    assert result == 0
    output = capsys.readouterr().out
    assert "\nSource manifest created!" in output
    assert "  Path:" in output
    manifest_path = tmp_path / "manifests" / "interactive-book.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["book_title"] == "Interactive Book"
    assert manifest["ruleset"] == "DND 5.5e"
    assert manifest["extraction_settings"]["preferred_methods"] == ["pdf_text_layer", "local_ocr"]
    assert manifest["extraction_settings"]["allow_llm_vision"] is False


def test_cli_create_manifest_interactive_sets_llm_allowed_when_preferred(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF fixture content")
    answers = iter(
        [
            "y",
            "LLM Book",
            "DND 5.5e",
            str(pdf_path),
            "",
            "",
            "",
            "",
            "pdf_text_layer,llm_vision_text",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    result = main(["source-manifest", "create", "--output-dir", str(tmp_path / "manifests")])

    assert result == 0
    output = capsys.readouterr().out
    assert "allow_llm_vision will be true" in output
    manifest_path = tmp_path / "manifests" / "llm-book.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["extraction_settings"]["preferred_methods"] == [
        "pdf_text_layer",
        "llm_vision_text",
    ]
    assert manifest["extraction_settings"]["allow_llm_vision"] is True


def test_cli_create_manifest_interactive_reports_missing_source_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    answers = iter(
        [
            "y",
            "Missing Interactive Book",
            "DND 5.5e",
            str(tmp_path / "missing.pdf"),
            "",
            "",
            "",
            "",
            "",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    result = main(["source-manifest", "create", "--output-dir", str(tmp_path / "manifests")])

    assert result == 1
    error_output = capsys.readouterr().err
    assert "\nSource manifest creation failed :C" in error_output
    assert "Source PDF file was not located" in error_output
