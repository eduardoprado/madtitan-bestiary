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
    assert monster.gear == []
    assert monster.challenge is not None
    assert monster.challenge.lair_xp is None
    assert monster.has_bonus_actions is False
    assert monster.bonus_actions == []
    assert monster.has_reactions is False
    assert monster.reactions == []
    assert monster.legendary_status == "ordinary"
    assert monster.legendary_resistance is None
    assert monster.legendary_action_uses is None
    assert monster.has_lair_variant is False
    assert monster.legendary_actions == []
    assert monster.lair_actions == []
    assert monster.damage_types_dealt == ["Piercing"]
    assert monster.conditions_inflicted == ["Prone"]


def test_lich_structure_fixture_matches_contract() -> None:
    fixture_path = (
        Path(__file__).parents[4] / "samples" / "fixtures" / "srd" / "lich_2024_structure.json"
    )

    monster = MonsterOccurrence.model_validate_json(fixture_path.read_text())

    assert monster.name == "Lich"
    assert monster.creature_type == "undead"
    assert monster.creature_group == "wizard"
    assert monster.habitats == ["any"]
    assert monster.content_flags.has_image is True
    assert monster.content_flags.has_lore is True
    assert monster.challenge is not None
    assert monster.challenge.rating == "21"
    assert monster.challenge.xp == 33000
    assert monster.challenge.lair_xp == 41000
    assert monster.gear == ["Component Pouch"]
    assert monster.damage_resistances == ["Cold", "Lightning"]
    assert monster.damage_immunities == ["Necrotic", "Poison"]
    assert "Paralyzed" in monster.condition_immunities
    assert monster.has_spellcasting is True
    assert monster.has_bonus_actions is False
    assert monster.has_reactions is True
    assert len(monster.reactions) == 1
    assert monster.legendary_status == "legendary"
    assert monster.legendary_resistance is not None
    assert monster.legendary_resistance.uses == 4
    assert monster.legendary_resistance.lair_uses == 5
    assert monster.legendary_action_uses is not None
    assert monster.legendary_action_uses.uses == 3
    assert monster.legendary_action_uses.lair_uses == 4
    assert monster.has_lair_variant is True
    assert len(monster.legendary_actions) == 3
    assert monster.lair_actions == []
    assert monster.damage_types_dealt == ["Cold", "Force", "Necrotic"]
    assert monster.conditions_inflicted == ["Paralyzed"]


def test_adult_red_dragon_structure_fixture_matches_contract() -> None:
    fixture_path = (
        Path(__file__).parents[4]
        / "samples"
        / "fixtures"
        / "srd"
        / "adult_red_dragon_2024_structure.json"
    )

    monster = MonsterOccurrence.model_validate_json(fixture_path.read_text())

    assert monster.name == "Adult Red Dragon"
    assert monster.creature_type == "dragon"
    assert monster.creature_group == "chromatic"
    assert monster.habitats == ["hill", "mountain"]
    assert monster.content_flags.has_image is True
    assert monster.content_flags.has_lore is True
    assert monster.challenge is not None
    assert monster.challenge.rating == "17"
    assert monster.challenge.lair_xp == 20000
    assert monster.has_spellcasting is True
    assert monster.has_bonus_actions is False
    assert monster.has_reactions is False
    assert monster.damage_immunities == ["Fire"]
    assert monster.legendary_resistance is not None
    assert monster.legendary_resistance.uses == 3
    assert monster.legendary_action_uses is not None
    assert monster.legendary_action_uses.lair_uses == 4
    assert monster.has_lair_variant is True
    assert monster.lair_actions == []

    rend = next(feature for feature in monster.features if feature.name == "Rend")
    assert rend.attack is not None
    assert len(rend.attack.damage) == 2
    assert [damage.damage_type for damage in rend.attack.damage] == ["Slashing", "Fire"]

    fire_breath = next(feature for feature in monster.features if feature.name == "Fire Breath")
    assert fire_breath.recharge is not None
    assert fire_breath.recharge.minimum == 5
    assert fire_breath.recharge.maximum == 6
    assert fire_breath.area is not None
    assert fire_breath.area.shape == "cone"
    assert fire_breath.area.size == 60
    assert fire_breath.saving_throw is not None
    assert fire_breath.saving_throw.ability == "Dexterity"
    assert fire_breath.damage[0].damage_type == "Fire"
    assert monster.damage_types_dealt == ["Fire", "Slashing"]
    assert monster.conditions_inflicted == []


def test_reloader_synthetic_fixture_matches_contract() -> None:
    fixture_path = Path(__file__).parents[4] / "samples" / "synthetic" / "reloader_structure.json"

    monster = MonsterOccurrence.model_validate_json(fixture_path.read_text())

    assert monster.name == "Reloader"
    assert monster.creature_type == "aberration"
    assert monster.creature_group == "debuggers"
    assert monster.habitats == ["underdark"]
    assert monster.condition_immunities == ["Prone"]
    assert monster.has_bonus_actions is True
    assert monster.has_reactions is False
    assert monster.has_spellcasting is False
    assert monster.has_lair_variant is True

    fly = next(speed for speed in monster.speeds if speed.mode == "fly")
    assert fly.hover is True

    null_zone = monster.bonus_actions[0]
    assert null_zone.area is not None
    assert null_zone.area.shape == "cone"
    assert null_zone.area.size == 150

    patch_rays = next(feature for feature in monster.features if feature.name == "Patch Rays")
    assert len(patch_rays.options) == 10
    assert patch_rays.options[0].name == "Modal Prompt"
    assert patch_rays.options[0].conditions_inflicted == ["Charmed"]
    assert patch_rays.options[5].metadata["automatic_success_size"] == "Gargantuan"
    assert patch_rays.options[6].metadata["automatic_success_creature_types"] == [
        "construct",
        "undead",
    ]

    assert len(monster.legendary_actions) == 2
    assert monster.legendary_actions[0].metadata["attack"] == "Null Bite"
    assert monster.damage_types_dealt == ["Force", "Necrotic", "Piercing", "Poison", "Psychic"]
    assert monster.conditions_inflicted == [
        "Charmed",
        "Frightened",
        "Paralyzed",
        "Petrified",
        "Poisoned",
        "Restrained",
        "Unconscious",
    ]
