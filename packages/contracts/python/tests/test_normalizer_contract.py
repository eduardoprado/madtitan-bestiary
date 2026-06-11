from pathlib import Path

from madtitan_contracts.candidate import MonsterCandidate
from madtitan_contracts.draft import MonsterOccurrenceDraft, QuarantineRecord
from madtitan_contracts.monster import MonsterOccurrence
from madtitan_contracts.normalizer import accept_draft, normalize_candidate


def test_normalize_candidate_creates_valid_draft_from_structured_fields() -> None:
    candidate = _candidate_with_structured_fields(_dire_wolf_payload())

    result = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(result, MonsterOccurrenceDraft)
    assert result.candidate_id == candidate.candidate_id
    assert result.normalization.method == "structured_fields"
    assert result.monster["name"] == "Dire Wolf"
    assert result.monster["provenance"]["source_id"] == "monster-manual-2024"
    assert result.monster["provenance"]["page_start"] == 352
    assert result.monster["raw_json"]["structured_fields"]["name"] == "Dire Wolf"


def test_accept_draft_returns_monster_occurrence() -> None:
    candidate = _candidate_with_structured_fields(_dire_wolf_payload())
    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate, min_confidence=0.5)

    assert isinstance(result, MonsterOccurrence)
    assert result.name == "Dire Wolf"
    assert result.creature_type == "beast"
    assert result.raw_json["structured_fields"]["name"] == "Dire Wolf"


def test_accept_draft_infers_challenge_proficiency_bonus_from_rating() -> None:
    payload = _dire_wolf_payload()
    assert isinstance(payload["challenge"], dict)
    payload["challenge"].pop("proficiency_bonus")
    candidate = _candidate_with_structured_fields(payload)

    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate)

    assert isinstance(result, MonsterOccurrence)
    assert result.challenge is not None
    assert result.challenge.proficiency_bonus == 2
    assert any(
        warning.code == "inferred_challenge_proficiency_bonus"
        for warning in draft.normalization.warnings
    )


def test_accept_draft_infers_ability_modifiers_saves_and_initiative_from_scores() -> None:
    payload = _dire_wolf_payload()
    payload.pop("initiative")
    for ability in payload["abilities"].values():
        ability.pop("modifier")
        ability.pop("saving_throw")
    candidate = _candidate_with_structured_fields(payload)

    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate)

    assert isinstance(result, MonsterOccurrence)
    assert result.abilities is not None
    assert result.abilities.str_.modifier == 3
    assert result.abilities.str_.saving_throw == 3
    assert result.abilities.dex.modifier == 2
    assert result.abilities.dex.saving_throw == 2
    assert result.initiative is not None
    assert result.initiative.bonus == 2
    assert result.initiative.static_value == 12
    assert any(warning.code == "inferred_dex_modifier" for warning in draft.normalization.warnings)
    assert any(warning.code == "inferred_initiative" for warning in draft.normalization.warnings)


def test_accept_draft_infers_lowest_ability_scores_from_modifiers() -> None:
    payload = _dire_wolf_payload()
    payload.pop("initiative")
    for ability in payload["abilities"].values():
        ability.pop("score")
        ability.pop("saving_throw")
    candidate = _candidate_with_structured_fields(payload)

    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate)

    assert isinstance(result, MonsterOccurrence)
    assert result.abilities is not None
    assert result.abilities.str_.score == 16
    assert result.abilities.dex.score == 14
    assert result.abilities.int_.score == 2
    assert result.abilities.cha.score == 6
    assert result.initiative is not None
    assert result.initiative.static_value == 12
    assert any(warning.code == "inferred_str_score" for warning in draft.normalization.warnings)


def test_accept_draft_defaults_alignment_when_not_provided() -> None:
    payload = _dire_wolf_payload()
    payload.pop("alignment")
    candidate = _candidate_with_structured_fields(payload)

    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate)

    assert isinstance(result, MonsterOccurrence)
    assert result.alignment == "not_provided"


def test_normalize_candidate_quarantines_missing_required_fields() -> None:
    payload = _dire_wolf_payload()
    payload.pop("name")
    candidate = _candidate_with_structured_fields(payload)

    result = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "contract_validation_failed"
    assert result.candidate_id == candidate.candidate_id
    assert any(error.path == "name" for error in result.errors)
    assert result.draft_payload["creature_type"] == "beast"
    assert result.repair.eligible_for_manual_review is True


def test_accept_draft_quarantines_valid_contract_without_challenge() -> None:
    payload = _dire_wolf_payload()
    payload.pop("challenge")
    candidate = _candidate_with_structured_fields(payload)
    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate, created_at="2026-06-11T05:31:00Z")

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "missing_required_field"
    assert any(error.path == "challenge" for error in result.errors)


def test_accept_draft_quarantines_valid_contract_without_combat_actions() -> None:
    payload = _dire_wolf_payload()
    payload["features"] = [
        feature
        for feature in payload["features"]
        if isinstance(feature, dict) and feature.get("kind") == "trait"
    ]
    candidate = _candidate_with_structured_fields(payload)
    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(draft, candidate=candidate, created_at="2026-06-11T05:31:00Z")

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "missing_combat_actions"
    assert result.errors[0].code == "missing_combat_actions"


def test_accept_draft_quarantines_valid_contract_without_raw_json() -> None:
    candidate = _candidate_with_structured_fields(_dire_wolf_payload())
    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(draft, MonsterOccurrenceDraft)
    draft.monster["raw_json"] = {}
    result = accept_draft(draft, candidate=candidate, created_at="2026-06-11T05:31:00Z")

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "missing_required_field"
    assert any(error.path == "raw_json" for error in result.errors)


def test_normalize_candidate_quarantines_candidate_without_structured_fields() -> None:
    candidate = _candidate_with_structured_fields({})

    result = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "missing_structured_fields"
    assert result.errors[0].path == "candidate.structured_fields"
    assert result.repair.eligible_for_ocr_retry is True


def test_accept_draft_quarantines_low_confidence_result() -> None:
    candidate = _candidate_with_structured_fields(_dire_wolf_payload(), confidence=0.25)
    draft = normalize_candidate(candidate, created_at="2026-06-11T05:30:00Z")

    assert isinstance(draft, MonsterOccurrenceDraft)
    result = accept_draft(
        draft,
        candidate=candidate,
        min_confidence=0.75,
        created_at="2026-06-11T05:31:00Z",
    )

    assert isinstance(result, QuarantineRecord)
    assert result.reason == "low_confidence"
    assert result.errors[0].path == "normalization.confidence"


def _dire_wolf_payload() -> dict[str, object]:
    fixture_path = (
        Path(__file__).parents[4] / "samples" / "fixtures" / "srd" / "dire_wolf_2024_structure.json"
    )
    monster = MonsterOccurrence.model_validate_json(fixture_path.read_text())
    payload = monster.model_dump(by_alias=True, mode="json")
    payload.pop("provenance")
    payload.pop("confidence")
    return payload


def _candidate_with_structured_fields(
    structured_fields: dict[str, object],
    *,
    confidence: float = 0.91,
) -> MonsterCandidate:
    return MonsterCandidate.model_validate(
        {
            "candidate_id": "mm2024-p0352-dire-wolf-candidate-v1",
            "status": "pending",
            "source": {
                "source_book_id": "monster-manual-2024",
                "book_title": "Monster Manual 2024",
                "ruleset": "DND 5.5e",
                "source_file_id": "mm2024-filehash",
                "source_file_checksum": "sha256:example",
                "page_start": 352,
                "page_end": 352,
                "page_labels": ["352"],
            },
            "source_format": {
                "profile_id": "mm2024-statblock",
                "profile_version": "v1",
                "statblock_family": "dnd_2024",
                "layout_type": "two_column_card",
                "expected_single_page": True,
                "column_count": 2,
                "section_order": ["header", "traits", "actions"],
                "heading_patterns": ["uppercase_red_heading"],
                "known_variations": [],
                "notes": "Manual fixture candidate for normalizer tests.",
                "metadata": {},
            },
            "lineage": {
                "extracted_page_text_ids": ["mm2024-filehash-p0352-text-v1"],
                "extraction_methods": ["manual_transcription"],
                "segmentation_run_id": "segment-run-test",
                "segmentation_method": "fixture_sections",
                "segmenter_version": "segmenter-v0.1.0",
                "parent_candidate_id": None,
                "repair_source_quarantine_record_id": None,
            },
            "candidate": {
                "name_hint": "Dire Wolf",
                "creature_type_hint": "beast",
                "structured_fields": structured_fields,
                "page_span_text": "synthetic candidate text",
                "page_span_text_ref": None,
                "sections": [],
                "start_marker": "DIRE WOLF",
                "end_marker": "ACTIONS",
                "raw_text_hash": "sha256:example",
            },
            "location": {
                "page_start": 352,
                "page_end": 352,
                "text_start_offset": 0,
                "text_end_offset": 1000,
                "bounding_boxes": [],
            },
            "quality": {
                "confidence": confidence,
                "text_quality": "good",
                "segmentation_quality": "complete",
                "warnings": [],
            },
            "normalization": {
                "recommended_method": "structured_fields",
                "attempt_count": 0,
                "last_attempt_at": None,
            },
            "audit": {
                "created_at": "2026-06-11T05:10:00Z",
                "created_by": "candidate_segmentation",
                "private_content": False,
                "updated_at": None,
            },
        }
    )
