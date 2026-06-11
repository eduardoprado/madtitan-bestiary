from pathlib import Path

from madtitan_contracts.monster import MonsterOccurrence


def test_dire_wolf_structure_fixture_matches_contract() -> None:
    fixture_path = (
        Path(__file__).parents[4] / "samples" / "fixtures" / "srd" / "dire_wolf_2024_structure.json"
    )

    monster = MonsterOccurrence.model_validate_json(fixture_path.read_text())

    assert monster.name == "Dire Wolf"
    assert monster.creature_type == "beast"
    assert monster.creature_group is None
    assert monster.habitats == ["forest"]
    assert monster.provenance.page_start == 352
    assert monster.armor_class is not None
    assert monster.armor_class.value == 14
    assert monster.armor_class.source == "non-specified"
    assert monster.abilities is not None
    assert monster.abilities.dex.score == 15
    assert monster.abilities.int_.modifier == -4
    assert monster.hit_point_formula is not None
    assert monster.hit_point_formula.quantity == 3
    assert monster.legendary_status == "ordinary"
    assert monster.legendary_actions == []
    assert monster.lair_actions == []
    assert monster.damage_types_dealt == ["Piercing"]
    assert monster.conditions_inflicted == ["Prone"]
