from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from madtitan_contracts.candidate import MonsterCandidate
from madtitan_contracts.draft import (
    MonsterOccurrenceDraft,
    NormalizationMetadata,
    NormalizationWarning,
    QuarantineAudit,
    QuarantineError,
    QuarantineRecord,
    QuarantineRepair,
    QuarantineSource,
)
from madtitan_contracts.inference import infer_monster_payload
from madtitan_contracts.monster import MonsterOccurrence, SourceProvenance
from madtitan_contracts.policy import (
    DEFAULT_ACCEPTANCE_POLICY,
    AcceptancePolicy,
    acceptance_reason,
)


DEFAULT_NORMALIZER_VERSION = "normalizer-v0.1.0"


def normalize_candidate(
    candidate: MonsterCandidate,
    *,
    method: str = "structured_fields",
    normalizer_version: str = DEFAULT_NORMALIZER_VERSION,
    run_id: str | None = None,
    created_at: str | None = None,
) -> MonsterOccurrenceDraft | QuarantineRecord:
    """Create a draft from a candidate, or quarantine it when required fields are absent.

    This first implementation expects hand-authored or pre-parsed structured fields on
    the candidate. Later source-specific normalizers can produce the same draft shape
    from raw section text.
    """

    timestamp = created_at or _utc_now()
    normalization_run_id = run_id or f"normalize-{candidate.candidate_id}"

    if not candidate.candidate.structured_fields:
        return _quarantine(
            candidate=candidate,
            draft=None,
            reason="missing_structured_fields",
            errors=[
                QuarantineError(
                    path="candidate.structured_fields",
                    message="No structured fields were available to build a monster draft.",
                    code="missing_structured_fields",
                )
            ],
            parser_version=normalizer_version,
            created_at=timestamp,
            eligible_for_llm_repair=True,
        )

    monster_payload = dict(candidate.candidate.structured_fields)
    monster_payload.setdefault(
        "provenance",
        _provenance_from_candidate(candidate, normalizer_version).model_dump(mode="json"),
    )
    monster_payload.setdefault("confidence", candidate.quality.confidence)
    monster_payload, inference_warnings = infer_monster_payload(
        monster_payload,
        raw_json_fallback={"structured_fields": candidate.candidate.structured_fields},
    )

    draft = MonsterOccurrenceDraft(
        draft_id=f"{candidate.candidate_id}-draft-v1",
        candidate_id=candidate.candidate_id,
        normalization=NormalizationMetadata(
            method=method,
            normalizer_version=normalizer_version,
            run_id=normalization_run_id,
            confidence=candidate.quality.confidence,
            warnings=inference_warnings,
        ),
        monster=monster_payload,
    )

    try:
        MonsterOccurrence.model_validate(draft.monster)
    except ValidationError as error:
        return _quarantine(
            candidate=candidate,
            draft=draft,
            reason="contract_validation_failed",
            errors=_validation_errors(error),
            parser_version=normalizer_version,
            created_at=timestamp,
            eligible_for_llm_repair=True,
        )

    return draft


def accept_draft(
    draft: MonsterOccurrenceDraft,
    *,
    candidate: MonsterCandidate | None = None,
    min_confidence: float = 0,
    policy: AcceptancePolicy | None = None,
    created_at: str | None = None,
) -> MonsterOccurrence | QuarantineRecord:
    """Validate a draft and return the accepted occurrence or a quarantine record."""

    timestamp = created_at or _utc_now()
    acceptance_policy = policy or DEFAULT_ACCEPTANCE_POLICY
    min_confidence = max(min_confidence, acceptance_policy.min_confidence)

    if draft.normalization.confidence < min_confidence:
        return _quarantine(
            candidate=candidate,
            draft=draft,
            reason="low_confidence",
            errors=[
                QuarantineError(
                    path="normalization.confidence",
                    message=(
                        f"Draft confidence {draft.normalization.confidence} is below "
                        f"the acceptance threshold {min_confidence}."
                    ),
                    code="low_confidence",
                )
            ],
            parser_version=draft.normalization.normalizer_version,
            created_at=timestamp,
            eligible_for_llm_repair=False,
        )

    draft = _draft_with_inference(draft)

    try:
        monster = MonsterOccurrence.model_validate(draft.monster)
    except ValidationError as error:
        return _quarantine(
            candidate=candidate,
            draft=draft,
            reason="contract_validation_failed",
            errors=_validation_errors(error),
            parser_version=draft.normalization.normalizer_version,
            created_at=timestamp,
            eligible_for_llm_repair=True,
        )

    policy_errors = acceptance_policy.evaluate(monster, raw_payload=draft.monster)
    if policy_errors:
        return _quarantine(
            candidate=candidate,
            draft=draft,
            reason=acceptance_reason(policy_errors),
            errors=policy_errors,
            parser_version=draft.normalization.normalizer_version,
            created_at=timestamp,
            eligible_for_llm_repair=False,
        )

    return monster


def _draft_with_inference(draft: MonsterOccurrenceDraft) -> MonsterOccurrenceDraft:
    inferred_payload, inference_warnings = infer_monster_payload(draft.monster)
    if not inference_warnings:
        return draft

    return draft.model_copy(
        update={
            "normalization": draft.normalization.model_copy(
                update={
                    "warnings": [
                        *draft.normalization.warnings,
                        *_dedupe_warnings(draft.normalization.warnings, inference_warnings),
                    ]
                }
            ),
            "monster": inferred_payload,
        }
    )


def _dedupe_warnings(
    existing: list[NormalizationWarning],
    incoming: list[NormalizationWarning],
) -> list[NormalizationWarning]:
    existing_codes = {warning.code for warning in existing}
    return [warning for warning in incoming if warning.code not in existing_codes]


def _provenance_from_candidate(
    candidate: MonsterCandidate,
    normalizer_version: str,
) -> SourceProvenance:
    extraction_method = "+".join(candidate.lineage.extraction_methods) or "unknown"
    return SourceProvenance(
        source_id=candidate.source.source_book_id,
        source_title=candidate.source.book_title,
        book_title=candidate.source.book_title,
        ruleset=candidate.source.ruleset,
        page_start=candidate.source.page_start,
        page_end=candidate.source.page_end,
        extraction_method=extraction_method,
        parser_version=normalizer_version,
    )


def _quarantine(
    *,
    candidate: MonsterCandidate | None,
    draft: MonsterOccurrenceDraft | None,
    reason: str,
    errors: list[QuarantineError],
    parser_version: str,
    created_at: str,
    eligible_for_llm_repair: bool,
) -> QuarantineRecord:
    candidate_id = candidate.candidate_id if candidate else draft.candidate_id if draft else None
    draft_id = draft.draft_id if draft else None
    source = _quarantine_source(candidate, draft)
    return QuarantineRecord(
        quarantine_record_id=_quarantine_record_id(candidate_id, draft_id, reason),
        candidate_id=candidate_id,
        draft_id=draft_id,
        reason=reason,
        severity="review_required",
        source=source,
        errors=errors,
        raw_candidate_ref=f"raw.monster_candidate:{candidate_id}" if candidate_id else None,
        draft_payload=draft.monster if draft else {},
        repair=QuarantineRepair(
            eligible_for_manual_review=True,
            eligible_for_ocr_retry=reason == "missing_structured_fields",
            eligible_for_llm_repair=eligible_for_llm_repair,
            next_recommended_step="manual_review",
        ),
        audit=QuarantineAudit(
            created_at=created_at,
            parser_version=parser_version,
            private_content=candidate.audit.private_content if candidate else True,
        ),
    )


def _quarantine_source(
    candidate: MonsterCandidate | None,
    draft: MonsterOccurrenceDraft | None,
) -> QuarantineSource:
    if candidate:
        return QuarantineSource(
            source_book_id=candidate.source.source_book_id,
            book_title=candidate.source.book_title,
            ruleset=candidate.source.ruleset,
            source_file_id=candidate.source.source_file_id,
            page_start=candidate.source.page_start,
            page_end=candidate.source.page_end,
        )

    provenance = _draft_provenance(draft)
    return QuarantineSource(
        source_book_id=provenance.get("source_id"),
        book_title=provenance.get("book_title") or provenance.get("source_title"),
        ruleset=provenance.get("ruleset"),
        page_start=provenance.get("page_start"),
        page_end=provenance.get("page_end"),
    )


def _draft_provenance(draft: MonsterOccurrenceDraft | None) -> dict[str, Any]:
    if draft is None:
        return {}
    provenance = draft.monster.get("provenance")
    return provenance if isinstance(provenance, dict) else {}


def _validation_errors(error: ValidationError) -> list[QuarantineError]:
    return [
        QuarantineError(
            path=_format_path(issue["loc"]),
            message=issue["msg"],
            code=issue["type"],
        )
        for issue in error.errors()
    ]


def _format_path(location: tuple[int | str, ...]) -> str | None:
    if not location:
        return None
    return ".".join(str(part) for part in location)


def _quarantine_record_id(candidate_id: str | None, draft_id: str | None, reason: str) -> str:
    source_id = draft_id or candidate_id or "unknown"
    return f"quarantine-{source_id}-{reason}"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
