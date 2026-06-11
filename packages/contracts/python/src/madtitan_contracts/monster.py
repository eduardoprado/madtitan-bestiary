from typing import Literal

from pydantic import BaseModel, Field


CreatureType = Literal[
    "aberration",
    "beast",
    "celestial",
    "construct",
    "dragon",
    "elemental",
    "fey",
    "fiend",
    "giant",
    "humanoid",
    "monstrosity",
    "ooze",
    "plant",
    "undead",
]

Habitat = Literal[
    "any",
    "arctic",
    "coastal",
    "desert",
    "forest",
    "grassland",
    "hill",
    "mountain",
    "swamp",
    "underdark",
    "underwater",
    "urban",
]


class SourceProvenance(BaseModel):
    """Where this monster occurrence came from."""

    source_id: str
    source_title: str
    book_title: str | None = None
    ruleset: str | None = None
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    extraction_method: str
    parser_version: str


class ContentFlags(BaseModel):
    """Source-page content flags useful for private UI and extraction QA."""

    has_image: bool = False
    has_lore: bool = False


class ExtendedAttribute(BaseModel):
    """Optional normalized attribute promoted from a source-specific field."""

    key: str
    label: str | None = None
    value: str | int | float | bool | list[str] | None = None
    status: str = "source_provided"
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None


class DiceFormula(BaseModel):
    """Parsed dice expression such as 3d10+6."""

    raw: str
    quantity: int = Field(ge=0)
    die_type: str = Field(pattern=r"^d\d+$")
    modifier: int = 0


class MovementSpeed(BaseModel):
    """A speed entry. Unlabeled stat-block speed should use mode='walk'."""

    mode: str = "walk"
    distance: int = Field(ge=0)
    unit: str = "ft"
    hover: bool = False


class Initiative(BaseModel):
    bonus: int
    static_value: int


class ArmorClass(BaseModel):
    value: int = Field(ge=0)
    source: str = "non-specified"


class AbilityBlock(BaseModel):
    score: int = Field(ge=1, le=30)
    modifier: int
    saving_throw: int | None = None


class AbilityScores(BaseModel):
    str_: AbilityBlock = Field(alias="str")
    dex: AbilityBlock
    con: AbilityBlock
    int_: AbilityBlock = Field(alias="int")
    wis: AbilityBlock
    cha: AbilityBlock


class SkillBonus(BaseModel):
    name: str
    modifier: int


class Sense(BaseModel):
    name: str
    distance: int | None = Field(default=None, ge=0)
    unit: str | None = "ft"


class Challenge(BaseModel):
    rating: str
    xp: int | None = Field(default=None, ge=0)
    lair_xp: int | None = Field(default=None, ge=0)
    proficiency_bonus: int | None = None


class LegendaryResistance(BaseModel):
    uses: int = Field(ge=0)
    lair_uses: int | None = Field(default=None, ge=0)


class LegendaryActionUses(BaseModel):
    uses: int = Field(ge=0)
    lair_uses: int | None = Field(default=None, ge=0)
    regain_timing: str | None = None


class SavingThrowEffect(BaseModel):
    ability: str
    dc: int | None = Field(default=None, ge=0)
    success: str | None = None
    failure: str | None = None


class RechargeRule(BaseModel):
    type: str
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    text: str | None = None


class AreaEffect(BaseModel):
    shape: str
    size: int | None = Field(default=None, ge=0)
    unit: str | None = "ft"
    text: str | None = None


class DamageInstance(BaseModel):
    average: int | None = Field(default=None, ge=0)
    formula: DiceFormula | None = None
    damage_type: str | None = None


class AttackDetail(BaseModel):
    attack_type: str | None = None
    attack_roll_bonus: int | None = None
    reach: int | None = Field(default=None, ge=0)
    reach_unit: str | None = "ft"
    range_normal: int | None = Field(default=None, ge=0)
    range_long: int | None = Field(default=None, ge=0)
    damage: list[DamageInstance] = Field(default_factory=list)
    target_size_limit: str | None = None


class FeatureOption(BaseModel):
    label: str
    name: str
    text: str
    saving_throw: SavingThrowEffect | None = None
    damage: list[DamageInstance] = Field(default_factory=list)
    damage_types: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class MonsterFeature(BaseModel):
    name: str
    kind: str
    text: str
    attack: AttackDetail | None = None
    saving_throw: SavingThrowEffect | None = None
    recharge: RechargeRule | None = None
    area: AreaEffect | None = None
    damage: list[DamageInstance] = Field(default_factory=list)
    damage_types: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)
    options: list[FeatureOption] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class MonsterOccurrence(BaseModel):
    """Draft parser contract for one source-specific monster occurrence."""

    name: str
    size: str
    creature_type: CreatureType
    creature_group: str | None = None
    alignment: str | None = None
    habitats: list[Habitat] = Field(default_factory=list)
    armor_class: ArmorClass | None = None
    hit_points: int | None = Field(default=None, ge=0)
    hit_point_formula: DiceFormula | None = None
    speeds: list[MovementSpeed] = Field(default_factory=list)
    initiative: Initiative | None = None
    abilities: AbilityScores | None = None
    skills: list[SkillBonus] = Field(default_factory=list)
    senses: list[Sense] = Field(default_factory=list)
    passive_perception: int | None = Field(default=None, ge=0)
    languages: list[str] = Field(default_factory=list)
    languages_text: str | None = None
    gear: list[str] = Field(default_factory=list)
    damage_resistances: list[str] = Field(default_factory=list)
    damage_immunities: list[str] = Field(default_factory=list)
    condition_immunities: list[str] = Field(default_factory=list)
    challenge: Challenge | None = None
    features: list[MonsterFeature] = Field(default_factory=list)
    has_spellcasting: bool = False
    has_bonus_actions: bool = False
    bonus_actions: list[MonsterFeature] = Field(default_factory=list)
    has_reactions: bool = False
    reactions: list[MonsterFeature] = Field(default_factory=list)
    legendary_status: str = "ordinary"
    legendary_resistance: LegendaryResistance | None = None
    legendary_action_uses: LegendaryActionUses | None = None
    has_lair_variant: bool = False
    legendary_actions: list[MonsterFeature] = Field(default_factory=list)
    lair_actions: list[MonsterFeature] = Field(default_factory=list)
    content_flags: ContentFlags = Field(default_factory=ContentFlags)
    damage_types_dealt: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    provenance: SourceProvenance
    confidence: float = Field(ge=0, le=1)
    extended_attributes: dict[str, ExtendedAttribute] = Field(default_factory=dict)
    source_specific_fields: dict[str, object] = Field(default_factory=dict)
    raw_json: dict[str, object] = Field(default_factory=dict)
