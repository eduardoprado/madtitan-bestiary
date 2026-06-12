# Pipeline Extraction TODO

This file tracks the missing work needed to turn the current contracts and fixtures
into an executable private-first extraction pipeline.

The current project already has contracts for:

- `SourceBook`
- `ExtractedPageText`
- `PageContentAnnotation`
- `MonsterCandidate`
- `MonsterOccurrenceDraft`
- `MonsterOccurrence`
- `QuarantineRecord`

The pipeline work below should produce those objects from local/private PDFs and keep
real extracted source text out of git.

## 1. Source Manifest Loader

Goal: load user-provided book metadata and extraction settings before touching the PDF.

Status: v1 complete.

Remaining future refinements:

- Add source-specific extraction settings only after real PDFs prove they are needed.
- Add optional remote/private object references when the storage layer exists.

Plan:

- Use `uv run madtitan-pipelines source-manifest create` before each new extraction.
- Keep the generated manifests in ignored `data/source_manifests/` unless they are
  synthetic/redacted fixtures.
- Use `uv run madtitan-pipelines source-manifest validate data/source_manifests` before
  extraction.
- Use `uv run madtitan-pipelines source-manifest list` to inspect registered sources.
- Use `LOCAL_PDF_MIRROR` for relative PDF paths inside the private local bestiary folder.
- Later, connect this to optional R2 references.

Acceptance:

- A real PDF can be registered without extracting text. Done for local manifests.
- The loader can validate all source metadata with the contracts package. Done.
- The loader can list registered manifests. Done.
- The loader refuses duplicate `source_book_id` values. Done.
- The loader refuses accidental manifest overwrites. Done.
- Relative PDF paths can resolve through `LOCAL_PDF_MIRROR`. Done.
- No raw PDF content is copied into repo-tracked files.

## 2. PDF Page Inventory

Goal: scan each source PDF and create a page inventory before extraction attempts.

Missing work:

- Read page count, page labels, dimensions, and basic text-layer availability.
- Detect pages that likely need OCR.
- Store enough metadata to decide which extraction methods to run per page.
- Preserve page identity for later `ExtractedPageText` records.

Plan:

- Use a local PDF library for page enumeration and text-layer triage.
- Emit page inventory records internally first; formalize a contract only if needed.
- Include page dimensions because annotation and image crop bboxes depend on them.
- Treat the whole book as input, but keep page-level outputs.

Acceptance:

- A 200-300 page book can be inventoried quickly.
- Each page has stable page number/label/dimension metadata.
- Pages with no usable text layer can be routed to OCR.

## 3. Text Extraction Attempts

Goal: generate page-level `ExtractedPageText` records.

Missing work:

- Implement `pdf_text_layer` extraction.
- Implement `local_ocr` extraction for scanned or poor text-layer pages.
- Add private text storage through `text_ref`.
- Add layout block extraction with reading order and page-relative bboxes.
- Record extraction warnings and quality signals.
- Support failed attempts without text when warnings explain the failure.

Plan:

- First build `pdf_text_layer` extraction for all pages.
- Add quality heuristics: empty text, low character count, garbled text, odd ordering.
- Retry only flagged pages with `local_ocr`.
- Persist real page text outside git and store `text_ref` in the JSON record.
- Use inline text only for synthetic, redacted, or licensed fixtures.

Acceptance:

- A source book produces one `ExtractedPageText` attempt per page for text-layer
  extraction.
- OCR attempts are separate records, not replacements.
- `validate samples` keeps passing with extracted text fixture examples.
- Private extracted text is not committed.

## 4. LLM/Vision Text and Page Annotation Path

Goal: support approved LLM/vision use for difficult pages and image/lore ownership.

Missing work:

- Define when `llm_vision_text` is allowed.
- Define privacy and approval controls for sending page images to an LLM.
- Produce `PageContentAnnotation` records for monster image and lore detections.
- Capture lore extraction evidence as text/text_ref/text_hash plus block/span refs.
- Capture monster image bboxes as future crop inputs.

Plan:

- Keep LLM/vision disabled by default through source extraction settings.
- Only run it on pages selected by rules or explicit user approval.
- Store annotations as evidence, not accepted monster data.
- Let Candidate Normalization decide whether annotation lore becomes
  `MonsterOccurrence.lore`.
- Leave image cropping as a later asset generation step.

Acceptance:

- A page can have image/lore annotations linked to an `ExtractedPageText` ID.
- Annotation bboxes are sufficient to crop page-rendered images later.
- Lore text evidence can be stored by private `text_ref`.
- Annotation output does not directly mutate final monster records.

## 5. Candidate Segmentation

Goal: separate monster statblocks from non-monster pages.

Missing work:

- Read extracted page attempts for a whole book.
- Choose the best extraction attempt per page for segmentation.
- Detect likely monster statblock starts and ends.
- Emit zero, one, or many `MonsterCandidate` records.
- Support candidates spanning multiple pages.
- Ignore non-monster pages.

Plan:

- Start with source-specific segmentation profiles.
- For DND 2024-style sources, use heading patterns plus statblock markers such as
  AC, HP, Speed, ability rows, CR, actions, and legendary action sections.
- Preserve page lineage through `lineage.extracted_page_text_ids`.
- Add quarantine/debug metadata for ambiguous spans.
- Keep segmentation broad enough for later non-DND-2024 source layouts.

Acceptance:

- Monster pages produce candidates.
- Non-monster pages produce no candidates.
- Multi-page statblock fixtures are represented as one candidate with multiple page
  text IDs.
- Candidate fixtures still pass the candidate-to-occurrence pipeline tests.

## 6. Source-Specific Candidate Normalizers

Goal: turn segmented candidate text into structured `MonsterOccurrenceDraft` payloads.

Missing work:

- Build the first deterministic normalizer for DND 2024-style statblocks.
- Parse core fields: name, size, type, group, alignment, AC, HP, speed, abilities,
  skills, senses, languages, CR/PB, features, actions, reactions, bonus actions,
  legendary actions, lair variants, damage, conditions, lore, and content flags.
- Preserve raw parser output in `raw_json`.
- Convert page annotations into accepted occurrence fields only when association is
  confident enough.
- Quarantine unclear candidates.

Plan:

- Start with a narrow normalizer for the reviewed fixture shapes.
- Use deterministic parsers for structured statblock lines where possible.
- Keep spellcasting as feature metadata until the spells table exists.
- Use existing inference and acceptance policy before accepting a monster.
- Store unparsed or source-specific details in `source_specific_fields` or
  `extended_attributes`.

Acceptance:

- Dire Wolf-style candidates can be normalized without hand-authored
  `structured_fields`.
- Missing derived fields are filled by inference, not parser guesses.
- Invalid or incomplete drafts become `QuarantineRecord`.

## 7. Quarantine and Repair Loop

Goal: make failed extraction/segmentation/normalization records reviewable and reusable.

Missing work:

- Store quarantine records with clear reason codes.
- Link quarantine records back to source book, pages, candidates, and drafts.
- Support repair paths back into segmentation or normalization.
- Decide where repaired private text lives.

Plan:

- Use existing `QuarantineRecord` contract for normalization failures.
- Extend pipeline-level quarantine metadata if extraction and segmentation need their
  own failure categories.
- Keep repair IDs in lineage so repaired candidates can be traced.
- Add manual repair fixtures only with redacted/synthetic text.

Acceptance:

- Low-confidence and invalid records are excluded from accepted monster outputs.
- A quarantined candidate can be reprocessed without losing original lineage.
- Error messages are specific enough to guide parser improvements.

## 8. Storage and Loading

Goal: persist extraction outputs, raw pipeline records, and accepted monsters.

Missing work:

- Define raw Postgres tables for source books, page inventory, extracted page text
  metadata, annotations, candidates, drafts, validation results, and quarantine.
- Define storage conventions for private text refs and future image refs.
- Load accepted `MonsterOccurrence` records into core tables.
- Keep raw/private text out of public app surfaces unless explicitly allowed.

Plan:

- Store JSON payloads in raw tables first.
- Normalize accepted monster occurrence fields later through dbt models.
- Use object storage/local mirror for large private text and future cropped images.
- Keep database rows as metadata plus refs for large/private content.

Acceptance:

- Pipeline outputs can be reloaded idempotently.
- Accepted monsters are queryable separately from quarantined records.
- Private source text and image binaries are referenced, not stored directly in git.

## 9. Future Image Asset Extraction

Goal: crop detected monster images and link them to accepted monster occurrences.

Missing work:

- Render source PDF pages at a fixed DPI.
- Use `monster_image` annotation bboxes to crop image regions.
- Store cropped images in R2/S3-style object storage.
- Create a future `MonsterImageAsset` record with object ref, source bbox, page
  provenance, hash, dimensions, crop method, and confidence.
- Link image assets to accepted monster occurrences.

Plan:

- Do this after text/lore extraction is stable.
- Start with manually reviewed image bboxes.
- Keep object storage as the image source of truth; database stores refs and metadata.

Acceptance:

- A monster occurrence can point to one or more image assets.
- Crops are reproducible from source page, bbox, render DPI, and source checksum.

## 10. Future Monster Relationship Layer

Goal: connect same-monster renditions and related monsters across books.

Missing work:

- Decide whether relationships connect monster identities, occurrences, or both.
- Support relationship types such as same monster, variant, creates, created by,
  related lore, similar role, and manual association.
- Support confidence and provenance for relationship assertions.
- Decide whether Postgres tables are enough or whether a graph view/store is useful.

Plan:

- Keep all source-specific monsters as separate `MonsterOccurrence` records.
- Add relationship modeling after multiple books are ingested.
- Start in Postgres with relationship tables; generate graph views later if needed.

Acceptance:

- Different renditions of the same monster can be grouped.
- Related but distinct monsters can be connected without merging their occurrences.

## Suggested Build Order

1. Source manifest loader.
2. PDF page inventory.
3. PDF text-layer extraction.
4. Local OCR retry path.
5. Candidate segmentation for one source profile.
6. First source-specific normalizer.
7. Quarantine review loop.
8. Postgres raw/core loading.
9. LLM/vision annotation path.
10. Image asset extraction and relationship layer.

## Near-Term Definition of Done

The extraction layer is minimally useful when a local PDF plus source manifest can
produce validated `ExtractedPageText` records for every page, with private text stored
by reference and no raw source text committed.

The broader extraction pipeline is usable when those page records can produce
`MonsterCandidate` records, normalize accepted monsters, and quarantine unclear cases
with enough lineage to improve the parser.
