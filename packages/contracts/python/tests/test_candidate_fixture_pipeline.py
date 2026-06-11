from pathlib import Path

import pytest

from madtitan_contracts.candidate import MonsterCandidate
from madtitan_contracts.draft import MonsterOccurrenceDraft
from madtitan_contracts.monster import MonsterOccurrence
from madtitan_contracts.normalizer import accept_draft, normalize_candidate


@pytest.mark.parametrize(
    ("fixture_path", "expected_name"),
    [
        ("samples/candidates/srd/dire_wolf_candidate.json", "Dire Wolf"),
        ("samples/candidates/srd/lich_candidate.json", "Lich"),
        ("samples/candidates/srd/adult_red_dragon_candidate.json", "Adult Red Dragon"),
        ("samples/candidates/synthetic/reloader_candidate.json", "Reloader"),
    ],
)
def test_candidate_fixture_reaches_accepted_monster(
    fixture_path: str,
    expected_name: str,
) -> None:
    path = Path(__file__).parents[4] / fixture_path
    candidate = MonsterCandidate.model_validate_json(path.read_text())

    draft = normalize_candidate(candidate, created_at="2026-06-11T06:10:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)

    monster = accept_draft(draft, candidate=candidate, created_at="2026-06-11T06:11:00Z")
    assert isinstance(monster, MonsterOccurrence)
    assert monster.name == expected_name
    assert monster.provenance.source_id == candidate.source.source_book_id
    assert monster.provenance.page_start == candidate.source.page_start
    assert monster.raw_json["structured_fields"]["name"] == expected_name


def test_dire_wolf_candidate_fixture_exercises_inference() -> None:
    path = Path(__file__).parents[4] / "samples/candidates/srd/dire_wolf_candidate.json"
    candidate = MonsterCandidate.model_validate_json(path.read_text())

    raw_dex = candidate.candidate.structured_fields["abilities"]["dex"]
    raw_initiative = candidate.candidate.structured_fields["initiative"]
    assert raw_dex == {"score": 15}
    assert raw_initiative == {"static_value": 12}

    draft = normalize_candidate(candidate, created_at="2026-06-11T06:10:00Z")
    assert isinstance(draft, MonsterOccurrenceDraft)
    warning_codes = {warning.code for warning in draft.normalization.warnings}
    assert "inferred_dex_modifier" in warning_codes
    assert "inferred_dex_saving_throw" in warning_codes
    assert "inferred_initiative_bonus" in warning_codes

    monster = accept_draft(draft, candidate=candidate, created_at="2026-06-11T06:11:00Z")
    assert isinstance(monster, MonsterOccurrence)
    assert monster.abilities is not None
    assert monster.abilities.dex.modifier == 2
    assert monster.abilities.dex.saving_throw == 2
    assert monster.initiative is not None
    assert monster.initiative.bonus == 2
    assert monster.initiative.static_value == 12
