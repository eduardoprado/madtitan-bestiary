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
- challenge rating, XP, and proficiency bonus
- traits
- actions
- legendary status, defaulting to `ordinary`
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
