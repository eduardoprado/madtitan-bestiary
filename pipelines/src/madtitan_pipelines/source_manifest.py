from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from madtitan_contracts.extraction import ExtractionMethod, ExtractionSettings, SourceBook


DEFAULT_MANIFEST_DIR = Path("data/source_manifests")
DEFAULT_PREFERRED_METHODS: list[ExtractionMethod] = ["pdf_text_layer", "local_ocr"]
PathInput = str | Path


class SourceFileNotFoundError(FileNotFoundError):
    """Raised when a source manifest points to a missing local PDF file."""


class DuplicateSourceBookIdError(ValueError):
    """Raised when multiple manifests declare the same source book id."""


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
    local_pdf_mirror: str | Path | None = None,
) -> SourceBook:
    """Build a validated SourceBook manifest row from user-provided metadata."""

    source_path = resolve_source_file_path(local_source_ref, local_pdf_mirror)
    validate_source_file(source_path)
    resolved_source_ref = str(source_path.resolve())
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


def write_source_manifest(
    source_book: SourceBook,
    output_dir: PathInput = DEFAULT_MANIFEST_DIR,
    *,
    overwrite: bool = False,
) -> Path:
    manifest_dir = coerce_path(output_dir)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    output_path = manifest_dir / f"{source_book.source_book_id}.json"
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Source manifest already exists: {output_path}. "
            "Choose a different source book id or remove the existing manifest."
        )
    output_path.write_text(json.dumps(source_book.model_dump(mode="json"), indent=2) + "\n")
    return output_path


def load_source_manifest(path: PathInput) -> SourceBook:
    manifest_path = coerce_path(path)
    return SourceBook.model_validate_json(manifest_path.read_text())


def load_source_manifests(path: PathInput) -> list[SourceBook]:
    manifest_paths = list_source_manifest_paths(path)
    manifests = [load_source_manifest(candidate) for candidate in manifest_paths]
    ensure_unique_source_book_ids(manifests)
    return manifests


def list_source_manifest_paths(path: PathInput) -> list[Path]:
    manifest_path = coerce_path(path)
    if manifest_path.is_file():
        return [manifest_path]
    if manifest_path.is_dir():
        return sorted(manifest_path.glob("*.json"))
    raise FileNotFoundError(f"Source manifest path does not exist: {manifest_path}")


def ensure_unique_source_book_ids(manifests: list[SourceBook]) -> None:
    seen_ids: dict[str, int] = {}
    duplicate_ids: list[str] = []
    for manifest in manifests:
        seen_ids[manifest.source_book_id] = seen_ids.get(manifest.source_book_id, 0) + 1
        if seen_ids[manifest.source_book_id] == 2:
            duplicate_ids.append(manifest.source_book_id)

    if duplicate_ids:
        raise DuplicateSourceBookIdError(
            "Duplicate source_book_id value(s): " + ", ".join(sorted(duplicate_ids))
        )


def resolve_source_file_path(
    local_source_ref: str,
    local_pdf_mirror: str | Path | None = None,
) -> Path:
    source_path = Path(local_source_ref).expanduser()
    if source_path.is_absolute() or local_pdf_mirror is None:
        return source_path
    return coerce_path(local_pdf_mirror) / source_path


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


def coerce_path(path: PathInput) -> Path:
    return Path(path).expanduser()
