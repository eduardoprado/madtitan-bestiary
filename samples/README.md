# Samples

Only synthetic, SRD, or clearly licensed fixtures belong here.

- `synthetic/`: invented test records that do not reproduce copyrighted text.
- `fixtures/srd/`: future SRD/CC-BY fixtures with provenance and license notes.
- `source_books/`: source manifest fixtures with user-provided book metadata and
  extraction settings.
- `extracted_text/`: redacted `ExtractedPageText` fixtures. Real extraction outputs
  should store text through private `text_ref` values.
- `annotations/`: page-level image/lore ownership hints, usually from approved
  vision-assisted review.
- `candidates/`: redacted `MonsterCandidate` fixtures that exercise the candidate
  normalization pipeline. These may include structured fields but must not include raw
  extracted commercial text.

Do not place raw PDFs, OCR output, extracted commercial text, or private exports in
this directory.
