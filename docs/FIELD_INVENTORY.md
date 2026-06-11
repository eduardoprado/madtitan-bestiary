# Field Inventory

This document records fields discovered while reviewing representative monsters. The
goal is to promote repeated, query-worthy fields into typed schema fields while keeping
rare or source-specific data in `source_specific_fields` until it proves reusable.

## Dire Wolf - Monster Manual 2024, page 352

Source/provenance fields identified:

- book title
- ruleset
- page start and end
- extraction method
- parser version
- content flags: monster image present, lore absent
- habitat enrichment from the book habitat section, separate from the stat block

Typed monster fields identified:

- name
- size
- creature type, constrained to the official type vocabulary
- optional creature group, replacing the earlier subtype naming
- habitats, allowing multiple common habitats per creature
- alignment
- armor class value and armor source, defaulting source to `non-specified`
- hit points
- hit point dice formula, decomposed into quantity, die type, and signed modifier
- speed entries, defaulting unlabeled speed to walking speed
- initiative bonus and static value
- each ability score, modifier, and saving throw
- skills and signed modifiers
- senses with optional distance
- passive perception
- language text and normalized language list
- gear as a generic list of text entries
- challenge rating, XP, lair XP when present, and proficiency bonus
- traits
- actions
- bonus action presence flag and bonus action list
- reaction presence flag and reaction list
- legendary status, defaulting to `ordinary`
- legendary resistance uses and lair uses when present
- lair variant flag
- legendary actions, empty when absent
- lair actions, empty when absent
- attack roll bonus
- reach/range
- damage average, dice formula, and damage type
- inflicted conditions
- derived damage types dealt
- derived conditions inflicted

Review notes:

- The screenshot shows Dex 15 / +2 / +2 and Int 3 / -4 / -4.
- Trait and action prose should be captured in private extraction outputs, but public
  fixtures should omit or paraphrase protected source text unless the exact source is
  clearly licensed for reuse.
- New fields from future PDFs should start in `source_specific_fields` when they are
  not yet common enough to become first-class typed fields.
- Dire Wolf habitat from the book-level habitat section is `forest`.

## Lich - Monster Manual 2024, page 196

Additional source/provenance fields identified:

- content flags: monster image present, lore present
- habitat enrichment: `any`

Additional typed monster fields identified:

- gear as a generic list of text entries
- damage resistances
- damage immunities
- condition immunities
- spellcasting presence flag
- reaction presence flag and reaction feature list
- bonus action presence flag and bonus action feature list
- lair XP and lair variant flag
- legendary resistance uses and lair uses
- legendary action uses and lair uses
- feature-level non-attack damage
- feature-level saving throw effect
- feature metadata for temporary structured details, including spellcasting groups

Review notes:

- Spellcasting remains a feature for now. Spell names and spell usage groups are kept
  in feature metadata until a spells table exists.
- Spell-mediated damage and conditions should not be added to derived monster fields
  until spell records are linked.
- The Lich has a lair variant and lair XP, but no explicit lair actions in this stat
  block.

## Adult Red Dragon - Monster Manual 2024, page 255

Additional source/provenance fields identified:

- content flags: monster image present, lore present
- habitat enrichment: `hill`, `mountain`

Additional typed monster fields identified:

- multiple movement speeds on one monster
- dragon creature group as `chromatic`
- damage immunity
- feature-level recharge rule
- feature-level area of effect
- multiple damage instances on a single attack
- spell attack bonus in spellcasting metadata
- material component requirement flag in spellcasting metadata
- legendary actions that call spellcasting or another named attack

Review notes:

- Do not create a separate dragon color field yet; the color is already present in the
  monster name.
- Spell-mediated conditions from Command are not included in derived conditions until
  the future spells table is linked.

## Reloader - Synthetic Non-SRD Transform

This fixture captures a complex non-SRD stat-block shape without committing protected
names, text, or exact values. It is intentionally coding-themed and stored under
`samples/synthetic/`.

Additional typed monster fields identified:

- fly speed hover flag
- bonus action area
- feature option tables for random sub-effects
- option-level saving throws
- option-level damage
- option-level directly inflicted conditions
- metadata for automatic-save cases and unusual riders
- legendary actions that reference existing attacks or option-table features

Review notes:

- The checked-in fixture is synthetic and should remain disconnected from any
  protected source name or prose.
- Directly described option conditions are included in top-level derived conditions.
- Bonus action effect prose remains redacted; only the area is structured for now.

## Controlled Vocabularies

Creature types:

- aberration
- beast
- celestial
- construct
- dragon
- elemental
- fey
- fiend
- giant
- humanoid
- monstrosity
- ooze
- plant
- undead

Habitats:

- any
- arctic
- coastal
- desert
- forest
- grassland
- hill
- mountain
- swamp
- underdark
- underwater
- urban

Known creature groups include angels, beholders, demons, devils, dinosaurs, dragons,
genies, goblinoids, lycanthropes, titans, and yugoloths. Groups are intentionally not
closed yet because more values will appear during field inventory.

## Future Improvements

- Add a spells table and link monster spellcasting features to canonical spell records.
  Spell-derived damage types and conditions should be added to monster derived fields
  only after this link exists.
