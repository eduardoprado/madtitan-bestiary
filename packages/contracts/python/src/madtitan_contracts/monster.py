from pydantic import BaseModel, Field


class SourceProvenance(BaseModel):
    """Where this monster occurrence came from."""

    source_id: str
    source_title: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    extraction_method: str
    parser_version: str


class AbilityScores(BaseModel):
    str_score: int = Field(ge=1, le=30)
    dex_score: int = Field(ge=1, le=30)
    con_score: int = Field(ge=1, le=30)
    int_score: int = Field(ge=1, le=30)
    wis_score: int = Field(ge=1, le=30)
    cha_score: int = Field(ge=1, le=30)


class MonsterFeature(BaseModel):
    name: str
    kind: str
    text: str


class MonsterOccurrence(BaseModel):
    """Draft parser contract for one source-specific monster occurrence."""

    name: str
    size: str
    creature_type: str
    alignment: str | None = None
    challenge_rating: str | None = None
    armor_class: int | None = Field(default=None, ge=0)
    hit_points: int | None = Field(default=None, ge=0)
    abilities: AbilityScores | None = None
    features: list[MonsterFeature] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    provenance: SourceProvenance
    confidence: float = Field(ge=0, le=1)
    raw_json: dict[str, object] = Field(default_factory=dict)
