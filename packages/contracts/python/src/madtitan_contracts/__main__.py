from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from madtitan_contracts.candidate import MonsterCandidate
from madtitan_contracts.monster import MonsterOccurrence


@dataclass
class ValidationSummary:
    accepted: int = 0
    failed: int = 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="madtitan_contracts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate monster occurrence and candidate JSON fixture files.",
    )
    validate_parser.add_argument(
        "paths",
        nargs="+",
        help="JSON file(s) or folder(s). Folders are scanned recursively for *.json files.",
    )

    args = parser.parse_args(argv)

    if args.command == "validate":
        return validate_paths([Path(path) for path in args.paths])

    parser.error(f"Unknown command: {args.command}")
    return 2


def validate_paths(paths: list[Path]) -> int:
    files = collect_json_files(paths)
    if not files:
        print("No JSON files found.", file=sys.stderr)
        return 2

    summary = ValidationSummary()
    for file_path in files:
        validate_file(file_path, summary)

    print()
    print(f"{summary.accepted} accepted, {summary.failed} failed")
    return 1 if summary.failed else 0


def collect_json_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        if path.is_dir():
            candidates = sorted(path.rglob("*.json"))
        elif path.is_file():
            candidates = [path]
        else:
            print(f"missing {path}", file=sys.stderr)
            continue

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)

    return files


def validate_file(file_path: Path, summary: ValidationSummary) -> None:
    try:
        payload = json.loads(file_path.read_text())
    except json.JSONDecodeError as error:
        summary.failed += 1
        print(f"failed {file_path}")
        print(f"  invalid JSON: {error.msg} at line {error.lineno}, column {error.colno}")
        return

    records = payload if isinstance(payload, list) else [payload]
    if not records:
        summary.failed += 1
        print(f"failed {file_path}")
        print("  expected one monster object or a non-empty array of monster objects")
        return

    for index, record in enumerate(records):
        label = f"{file_path}[{index}]" if isinstance(payload, list) else str(file_path)
        validate_record(label, record, summary)


def validate_record(label: str, record: Any, summary: ValidationSummary) -> None:
    if not isinstance(record, dict):
        summary.failed += 1
        print(f"failed {label}")
        print("  expected a JSON object")
        return

    try:
        contract_name, display_name = validate_contract_record(record)
    except ValidationError as error:
        summary.failed += 1
        print(f"failed {label}")
        for line in format_validation_error(error):
            print(f"  {line}")
        return

    summary.accepted += 1
    print(f"accepted {label} ({contract_name}: {display_name})")


def validate_contract_record(record: dict[str, Any]) -> tuple[str, str]:
    if "candidate_id" in record:
        candidate = MonsterCandidate.model_validate(record)
        display_name = candidate.candidate.name_hint or candidate.candidate_id
        return "MonsterCandidate", display_name

    monster = MonsterOccurrence.model_validate(record)
    return "MonsterOccurrence", monster.name


def format_validation_error(error: ValidationError) -> list[str]:
    lines: list[str] = []
    for issue in error.errors():
        location = ".".join(str(part) for part in issue["loc"])
        message = issue["msg"]
        lines.append(f"{location}: {message}" if location else message)
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
