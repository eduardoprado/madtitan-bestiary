from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from madtitan_contracts.extraction import ExtractionMethod, ExtractionSettings, SourceBook


DEFAULT_MANIFEST_DIR = Path("data/source_manifests")
DEFAULT_PREFERRED_METHODS: list[ExtractionMethod] = ["pdf_text_layer", "local_ocr"]


class SourceFileNotFoundError(FileNotFoundError):
    """Raised when a source manifest points to a missing local PDF file."""


def create_source_book(
    *,
    book_title: str,
    ruleset: str,
    local_source_ref: str,
    source_book_id: str | None = None,
    source_file_id: str | None = None,
    source_file_checksum: str | None = None,
    preferred_methods: list[ExtractionMethod] | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    render_dpi: int | None = 220,
    allow_llm_vision: bool = False,
) -> SourceBook:
    """Build a validated SourceBook manifest row from user-provided metadata."""

    source_path = Path(local_source_ref).expanduser()
    validate_source_file(source_path)
    resolved_source_ref = str(source_path.resolve()) if source_path.exists() else local_source_ref
    checksum = source_file_checksum or checksum_file(source_path)
    file_id = source_file_id or source_file_id_from_path(source_path, checksum)
    book_id = source_book_id or slugify(book_title)

    return SourceBook(
        source_book_id=book_id,
        book_title=book_title.strip(),
        ruleset=ruleset.strip(),
        source_file_id=file_id,
        source_file_checksum=checksum,
        local_source_ref=resolved_source_ref,
        private_source=True,
        extraction_settings=ExtractionSettings(
            preferred_methods=preferred_methods or DEFAULT_PREFERRED_METHODS,
            page_start=page_start,
            page_end=page_end,
            render_dpi=render_dpi,
            allow_llm_vision=allow_llm_vision,
            metadata={},
        ),
        metadata={
            "created_by": "madtitan-pipelines source-manifest create",
            "book_title_source": "user_provided",
            "ruleset_source": "user_provided",
        },
    )


def write_source_manifest(source_book: SourceBook, output_dir: Path = DEFAULT_MANIFEST_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{source_book.source_book_id}.json"
    output_path.write_text(json.dumps(source_book.model_dump(mode="json"), indent=2) + "\n")
    return output_path


def load_source_manifest(path: Path) -> SourceBook:
    return SourceBook.model_validate_json(path.read_text())


def load_source_manifests(path: Path) -> list[SourceBook]:
    if path.is_file():
        return [load_source_manifest(path)]
    if path.is_dir():
        return [load_source_manifest(candidate) for candidate in sorted(path.glob("*.json"))]
    raise FileNotFoundError(f"Source manifest path does not exist: {path}")


def validate_source_file(path: Path) -> None:
    if not path.exists():
        raise SourceFileNotFoundError(
            f"Source PDF file was not located at '{path}'. "
            "The path name may be different. Please add the file or correct the path and try again."
        )
    if not path.is_file():
        raise SourceFileNotFoundError(
            f"Source PDF path points to a directory, not a file: '{path}'. "
            "Please provide the full PDF file path and try again."
        )


def checksum_file(path: Path) -> str:
    validate_source_file(path)
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def source_file_id_from_path(path: Path, checksum: str) -> str:
    stem = slugify(path.stem) if path.stem else "source-pdf"
    checksum_suffix = checksum.removeprefix("sha256:")[:12]
    return f"{stem}-{checksum_suffix}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "source-book"
