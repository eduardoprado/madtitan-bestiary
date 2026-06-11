from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from typing import Any

from madtitan_contracts.draft import NormalizationWarning


def infer_monster_payload(
    payload: dict[str, Any],
    *,
    raw_json_fallback: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[NormalizationWarning]]:
    """Fill mechanically derived monster fields before quarantine decisions."""

    inferred = deepcopy(payload)
    warnings: list[NormalizationWarning] = []

    if not inferred.get("raw_json") and raw_json_fallback:
        inferred["raw_json"] = deepcopy(raw_json_fallback)
        warnings.append(_warning("inferred_raw_json", "Copied raw parser payload into raw_json."))

    _infer_challenge(inferred, warnings)
    _infer_abilities(inferred, warnings)
    _infer_initiative(inferred, warnings)
    _infer_section_flags(inferred, warnings)
    _infer_legendary_and_lair_flags(inferred, warnings)
    _infer_derived_effect_lists(inferred, warnings)

    return inferred, warnings


def _infer_challenge(payload: dict[str, Any], warnings: list[NormalizationWarning]) -> None:
    challenge = payload.get("challenge")
    if not isinstance(challenge, dict):
        return

    rating = challenge.get("rating")
    if challenge.get("proficiency_bonus") is None and isinstance(rating, str):
        proficiency_bonus = _proficiency_bonus_from_cr(rating)
        if proficiency_bonus is not None:
            challenge["proficiency_bonus"] = proficiency_bonus
            warnings.append(
                _warning(
                    "inferred_challenge_proficiency_bonus",
                    "Inferred challenge proficiency bonus from challenge rating.",
                )
            )


def _infer_abilities(payload: dict[str, Any], warnings: list[NormalizationWarning]) -> None:
    abilities = payload.get("abilities")
    if not isinstance(abilities, dict):
        return

    for ability_name in ["str", "dex", "con", "int", "wis", "cha"]:
        ability = abilities.get(ability_name)
        if not isinstance(ability, dict):
            continue

        score = ability.get("score")
        modifier = ability.get("modifier")

        if isinstance(score, int) and modifier is None:
            ability["modifier"] = _modifier_from_score(score)
            modifier = ability["modifier"]
            warnings.append(
                _warning(
                    f"inferred_{ability_name}_modifier",
                    f"Inferred {ability_name.upper()} modifier from ability score.",
                )
            )

        if isinstance(modifier, int) and score is None:
            inferred_score = _score_from_modifier(modifier)
            if inferred_score is not None:
                ability["score"] = inferred_score
                warnings.append(
                    _warning(
                        f"inferred_{ability_name}_score",
                        (
                            f"Inferred {ability_name.upper()} score from modifier using "
                            "the lowest score in the matching range."
                        ),
                    )
                )

        if ability.get("saving_throw") is None and isinstance(ability.get("modifier"), int):
            ability["saving_throw"] = ability["modifier"]
            warnings.append(
                _warning(
                    f"inferred_{ability_name}_saving_throw",
                    f"Defaulted {ability_name.upper()} saving throw to its modifier.",
                )
            )


def _infer_initiative(payload: dict[str, Any], warnings: list[NormalizationWarning]) -> None:
    initiative = payload.get("initiative")
    if isinstance(initiative, dict):
        bonus = initiative.get("bonus")
        static_value = initiative.get("static_value")

        if isinstance(static_value, int) and bonus is None:
            initiative["bonus"] = static_value - 10
            warnings.append(
                _warning("inferred_initiative_bonus", "Inferred initiative bonus from static value.")
            )
        elif isinstance(bonus, int) and static_value is None:
            initiative["static_value"] = 10 + bonus
            warnings.append(
                _warning(
                    "inferred_initiative_static_value",
                    "Inferred initiative static value from bonus.",
                )
            )
        return

    if initiative is not None:
        return

    abilities = payload.get("abilities")
    if not isinstance(abilities, dict):
        return

    dex = abilities.get("dex")
    if not isinstance(dex, dict) or not isinstance(dex.get("modifier"), int):
        return

    dex_modifier = dex["modifier"]
    payload["initiative"] = {
        "bonus": dex_modifier,
        "static_value": 10 + dex_modifier,
    }
    warnings.append(_warning("inferred_initiative", "Inferred initiative from Dexterity modifier."))


def _infer_section_flags(payload: dict[str, Any], warnings: list[NormalizationWarning]) -> None:
    if payload.get("bonus_actions") and payload.get("has_bonus_actions") is not True:
        payload["has_bonus_actions"] = True
        warnings.append(_warning("inferred_has_bonus_actions", "Inferred bonus action flag."))

    if payload.get("reactions") and payload.get("has_reactions") is not True:
        payload["has_reactions"] = True
        warnings.append(_warning("inferred_has_reactions", "Inferred reaction flag."))


def _infer_legendary_and_lair_flags(
    payload: dict[str, Any],
    warnings: list[NormalizationWarning],
) -> None:
    has_legendary_data = any(
        [
            payload.get("legendary_actions"),
            payload.get("legendary_action_uses"),
            payload.get("legendary_resistance"),
        ]
    )
    if has_legendary_data and payload.get("legendary_status") in {None, "ordinary"}:
        payload["legendary_status"] = "legendary"
        warnings.append(_warning("inferred_legendary_status", "Inferred legendary status."))

    challenge = payload.get("challenge")
    has_lair_data = bool(payload.get("lair_actions"))
    if isinstance(challenge, dict):
        has_lair_data = has_lair_data or challenge.get("lair_xp") is not None

    legendary_resistance = payload.get("legendary_resistance")
    if isinstance(legendary_resistance, dict):
        has_lair_data = has_lair_data or legendary_resistance.get("lair_uses") is not None

    legendary_action_uses = payload.get("legendary_action_uses")
    if isinstance(legendary_action_uses, dict):
        has_lair_data = has_lair_data or legendary_action_uses.get("lair_uses") is not None

    if has_lair_data and payload.get("has_lair_variant") is not True:
        payload["has_lair_variant"] = True
        warnings.append(_warning("inferred_has_lair_variant", "Inferred lair variant flag."))


def _infer_derived_effect_lists(
    payload: dict[str, Any],
    warnings: list[NormalizationWarning],
) -> None:
    features = []
    for key in ["features", "bonus_actions", "reactions", "legendary_actions", "lair_actions"]:
        value = payload.get(key)
        if isinstance(value, list):
            features.extend(item for item in value if isinstance(item, dict))

    damage_types = sorted(_collect_damage_types(features))
    if damage_types and not payload.get("damage_types_dealt"):
        payload["damage_types_dealt"] = damage_types
        warnings.append(_warning("inferred_damage_types_dealt", "Inferred dealt damage types."))

    conditions = sorted(_collect_conditions(features))
    if conditions and not payload.get("conditions_inflicted"):
        payload["conditions_inflicted"] = conditions
        warnings.append(_warning("inferred_conditions_inflicted", "Inferred inflicted conditions."))


def _collect_damage_types(features: list[dict[str, Any]]) -> set[str]:
    damage_types: set[str] = set()
    for feature in features:
        for damage_type in feature.get("damage_types", []):
            if isinstance(damage_type, str):
                damage_types.add(damage_type)
        _collect_damage_instances(feature.get("damage"), damage_types)
        attack = feature.get("attack")
        if isinstance(attack, dict):
            _collect_damage_instances(attack.get("damage"), damage_types)
        for option in feature.get("options", []):
            if not isinstance(option, dict):
                continue
            for damage_type in option.get("damage_types", []):
                if isinstance(damage_type, str):
                    damage_types.add(damage_type)
            _collect_damage_instances(option.get("damage"), damage_types)
    return damage_types


def _collect_damage_instances(value: Any, damage_types: set[str]) -> None:
    if not isinstance(value, list):
        return
    for damage in value:
        if isinstance(damage, dict) and isinstance(damage.get("damage_type"), str):
            damage_types.add(damage["damage_type"])


def _collect_conditions(features: list[dict[str, Any]]) -> set[str]:
    conditions: set[str] = set()
    for feature in features:
        for condition in feature.get("conditions_inflicted", []):
            if isinstance(condition, str):
                conditions.add(condition)
        for option in feature.get("options", []):
            if not isinstance(option, dict):
                continue
            for condition in option.get("conditions_inflicted", []):
                if isinstance(condition, str):
                    conditions.add(condition)
    return conditions


def _proficiency_bonus_from_cr(rating: str) -> int | None:
    try:
        challenge_rating = Fraction(rating)
    except ValueError:
        return None

    if challenge_rating <= 4:
        return 2
    if challenge_rating <= 8:
        return 3
    if challenge_rating <= 12:
        return 4
    if challenge_rating <= 16:
        return 5
    if challenge_rating <= 20:
        return 6
    if challenge_rating <= 24:
        return 7
    if challenge_rating <= 28:
        return 8
    if challenge_rating <= 30:
        return 9
    return None


def _modifier_from_score(score: int) -> int:
    return (score - 10) // 2


def _score_from_modifier(modifier: int) -> int | None:
    modifier_to_lowest_score = {
        -5: 1,
        -4: 2,
        -3: 4,
        -2: 6,
        -1: 8,
        0: 10,
        1: 12,
        2: 14,
        3: 16,
        4: 18,
        5: 20,
        6: 22,
        7: 24,
        8: 26,
        9: 28,
        10: 30,
    }
    return modifier_to_lowest_score.get(modifier)


def _warning(code: str, message: str) -> NormalizationWarning:
    return NormalizationWarning(code=code, message=message, severity="info")
