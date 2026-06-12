from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TextIO, cast

from madtitan_contracts.extraction import ExtractionMethod
from pydantic import ValidationError

from madtitan_pipelines.source_manifest import (
    DEFAULT_MANIFEST_DIR,
    DEFAULT_PREFERRED_METHODS,
    SourceFileNotFoundError,
    create_source_book,
    load_source_manifests,
    write_source_manifest,
)


EXTRACTION_METHOD_DESCRIPTIONS: dict[ExtractionMethod, str] = {
    "pdf_text_layer": "read embedded/selectable PDF text first; fastest when the PDF has usable text",
    "local_ocr": "render pages locally and run OCR; useful for scans or broken text layers",
    "llm_vision_text": "use an LLM vision pass to read page images; slower/costlier, useful for hard pages",
    "manual_transcription": "use human-entered text; mostly for fixtures or manual repair",
}

ANSI_GREEN_BOLD = "32;1"
ANSI_RED_BOLD = "31;1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="madtitan-pipelines")
    subparsers = parser.add_subparsers(dest="command", required=True)

    source_manifest_parser = subparsers.add_parser(
        "source-manifest",
        help="Create and validate private source book manifests.",
    )
    source_manifest_subparsers = source_manifest_parser.add_subparsers(
        dest="source_manifest_command",
        required=True,
    )

    create_parser = source_manifest_subparsers.add_parser(
        "create",
        help="Interactively create a SourceBook manifest before extraction.",
    )
    create_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_MANIFEST_DIR,
        help="Directory where the manifest JSON will be written. Defaults to ignored data/source_manifests.",
    )

    validate_parser = source_manifest_subparsers.add_parser(
        "validate",
        help="Validate one manifest file or a directory of manifest JSON files.",
    )
    validate_parser.add_argument("path", type=Path)

    args = parser.parse_args(argv)

    if args.command == "source-manifest" and args.source_manifest_command == "create":
        return create_manifest_interactive(args.output_dir)

    if args.command == "source-manifest" and args.source_manifest_command == "validate":
        return validate_manifest_path(args.path)

    parser.error("Unknown command")
    return 2


def create_manifest_interactive(output_dir: Path) -> int:
    if not prompt_bool("Would you like to extract a new book?", default=True):
        print("No manifest created.")
        return 0

    book_title = prompt_required("What is the book title?")
    ruleset = prompt_default("What ruleset is this book for?", "DND 5.5e")
    local_source_ref = prompt_required("What is the local PDF path?")
    source_book_id = prompt_default("Source book id", default_slug(book_title))
    page_start = prompt_optional_int("First page to extract? Leave blank for the whole PDF")
    page_end = prompt_optional_int("Last page to extract? Leave blank for the whole PDF")
    render_dpi = prompt_optional_int("Render DPI for OCR/image work", default=220)
    preferred_methods = prompt_preferred_methods(DEFAULT_PREFERRED_METHODS)
    if "llm_vision_text" in preferred_methods:
        allow_llm_vision = True
        print("LLM vision is included in preferred methods, so allow_llm_vision will be true.")
    else:
        allow_llm_vision = prompt_bool(
            "Allow LLM vision extraction/annotation as a fallback for this book?",
            default=False,
        )

    try:
        source_book = create_source_book(
            book_title=book_title,
            ruleset=ruleset,
            local_source_ref=local_source_ref,
            source_book_id=source_book_id,
            preferred_methods=preferred_methods,
            page_start=page_start,
            page_end=page_end,
            render_dpi=render_dpi,
            allow_llm_vision=allow_llm_vision,
        )
    except SourceFileNotFoundError as error:
        print_manifest_creation_failure(error)
        return 1
    except (FileNotFoundError, ValidationError) as error:
        print_manifest_creation_failure(error)
        return 1

    output_path = write_source_manifest(source_book, output_dir)
    print()
    print(color_text("Source manifest created!", ANSI_GREEN_BOLD, sys.stdout))
    print(f"  Path: {output_path}")
    print(f"  Source book id: {source_book.source_book_id}")
    print(f"  Checksum: {source_book.source_file_checksum}")
    return 0


def validate_manifest_path(path: Path) -> int:
    try:
        manifests = load_source_manifests(path)
    except (FileNotFoundError, ValidationError) as error:
        print(f"failed {path}")
        print(f"  {error}")
        return 1

    if not manifests:
        print(f"No manifest JSON files found in {path}", file=sys.stderr)
        return 2

    for manifest in manifests:
        print(f"accepted {manifest.source_book_id} ({manifest.book_title})")
    print()
    print(f"{len(manifests)} accepted, 0 failed")
    return 0


def prompt_required(question: str) -> str:
    while True:
        value = input(f"{question} ").strip()
        if value:
            return value
        print("This value is required.")


def prompt_default(question: str, default: str) -> str:
    value = input(f"{question} [{default}] ").strip()
    return value or default


def prompt_optional_int(question: str, default: int | None = None) -> int | None:
    default_hint = "" if default is None else f" [{default}]"
    while True:
        value = input(f"{question}{default_hint}: ").strip()
        if not value:
            return default
        try:
            parsed = int(value)
        except ValueError:
            print("Please enter a whole number or leave blank.")
            continue
        if parsed < 1:
            print("Please enter a number greater than zero.")
            continue
        return parsed


def prompt_preferred_methods(default: list[ExtractionMethod]) -> list[ExtractionMethod]:
    print("Preferred extraction methods:")
    for method, description in EXTRACTION_METHOD_DESCRIPTIONS.items():
        print(f"  - {method}: {description}")

    default_value = ",".join(default)
    allowed_methods = set(EXTRACTION_METHOD_DESCRIPTIONS)
    while True:
        value = input(
            "Choose methods in order, comma-separated "
            f"[{default_value}]: "
        ).strip()
        if not value:
            return list(default)

        methods = [method.strip() for method in value.split(",") if method.strip()]
        unknown_methods = [method for method in methods if method not in allowed_methods]
        if unknown_methods:
            print(f"Unknown extraction method(s): {', '.join(unknown_methods)}")
            print("Use one or more of the methods listed above.")
            continue

        deduped_methods = list(dict.fromkeys(methods))
        if not deduped_methods:
            print("Please choose at least one extraction method.")
            continue
        return cast(list[ExtractionMethod], deduped_methods)


def prompt_bool(question: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        value = input(f"{question} {suffix} ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def default_slug(value: str) -> str:
    from madtitan_pipelines.source_manifest import slugify

    return slugify(value)


def print_manifest_creation_failure(error: Exception) -> None:
    print(file=sys.stderr)
    print(color_text("Source manifest creation failed :C", ANSI_RED_BOLD, sys.stderr), file=sys.stderr)
    print(f"  {error}", file=sys.stderr)


def color_text(text: str, ansi_code: str, stream: TextIO) -> str:
    if os.environ.get("NO_COLOR") or not stream.isatty():
        return text
    return f"\033[{ansi_code}m{text}\033[0m"


if __name__ == "__main__":
    raise SystemExit(main())
