from typing import Any

from pydantic import BaseModel, Field

from madtitan_contracts.draft import QuarantineError
from madtitan_contracts.monster import MonsterOccurrence


class AcceptancePolicy(BaseModel):
    """Project-level completeness checks for accepting a monster occurrence."""

    required_top_level_fields: tuple[str, ...] = (
        "name",
        "size",
        "creature_type",
        "armor_class",
        "hit_points",
        "speeds",
        "abilities",
        "challenge",
        "provenance",
        "raw_json",
    )
    require_combat_actions: bool = True
    require_challenge_rating: bool = True
    require_challenge_proficiency_bonus: bool = True
    require_non_empty_raw_json: bool = True
    min_confidence: float = Field(default=0, ge=0, le=1)

    def evaluate(
        self,
        monster: MonsterOccurrence,
        *,
        raw_payload: dict[str, Any] | None = None,
    ) -> list[QuarantineError]:
        errors: list[QuarantineError] = []
        payload = raw_payload or monster.model_dump(by_alias=True, mode="json")

        for field_name in self.required_top_level_fields:
            if self._missing_field(monster, payload, field_name):
                errors.append(
                    QuarantineError(
                        path=field_name,
                        message=f"Required field '{field_name}' is missing or empty.",
                        code="missing_required_field",
                    )
                )

        if self.require_challenge_rating and (
            monster.challenge is None or not monster.challenge.rating
        ):
            errors.append(
                QuarantineError(
                    path="challenge.rating",
                    message="Challenge rating is required for acceptance.",
                    code="missing_required_field",
                )
            )

        if self.require_challenge_proficiency_bonus and (
            monster.challenge is None or monster.challenge.proficiency_bonus is None
        ):
            errors.append(
                QuarantineError(
                    path="challenge.proficiency_bonus",
                    message="Challenge proficiency bonus is required for acceptance.",
                    code="missing_required_field",
                )
            )

        if self.require_combat_actions and not _has_any_combat_section(monster):
            errors.append(
                QuarantineError(
                    path="features",
                    message=(
                        "At least one action, bonus action, reaction, legendary action, "
                        "or lair action is required."
                    ),
                    code="missing_combat_actions",
                )
            )

        return errors

    def _missing_field(
        self,
        monster: MonsterOccurrence,
        payload: dict[str, Any],
        field_name: str,
    ) -> bool:
        if field_name not in payload:
            return True

        value = getattr(monster, field_name)
        if value is None:
            return True
        if value == "":
            return True
        if isinstance(value, list) and not value:
            return True
        if (
            field_name == "raw_json"
            and self.require_non_empty_raw_json
            and isinstance(value, dict)
            and not value
        ):
            return True
        return False


DEFAULT_ACCEPTANCE_POLICY = AcceptancePolicy()


def acceptance_reason(errors: list[QuarantineError]) -> str:
    codes = {error.code for error in errors}
    if "missing_combat_actions" in codes:
        return "missing_combat_actions"
    if "missing_required_field" in codes:
        return "missing_required_field"
    return "needs_manual_review"


def _has_any_combat_section(monster: MonsterOccurrence) -> bool:
    return any(
        [
            any(feature.kind != "trait" for feature in monster.features),
            monster.bonus_actions,
            monster.reactions,
            monster.legendary_actions,
            monster.lair_actions,
        ]
    )
