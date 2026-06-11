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
    proficiency_bonus: int | None = None


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


class MonsterFeature(BaseModel):
    name: str
    kind: str
    text: str
    attack: AttackDetail | None = None
    damage_types: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)


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
    challenge: Challenge | None = None
    features: list[MonsterFeature] = Field(default_factory=list)
    legendary_status: str = "ordinary"
    legendary_actions: list[MonsterFeature] = Field(default_factory=list)
    lair_actions: list[MonsterFeature] = Field(default_factory=list)
    content_flags: ContentFlags = Field(default_factory=ContentFlags)
    damage_types_dealt: list[str] = Field(default_factory=list)
    conditions_inflicted: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    provenance: SourceProvenance
    confidence: float = Field(ge=0, le=1)
    source_specific_fields: dict[str, object] = Field(default_factory=dict)
    raw_json: dict[str, object] = Field(default_factory=dict)
