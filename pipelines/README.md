# Pipelines

Dagster assets for private-first ingestion, extraction, validation, and loading.

The v1 pipeline keeps copyrighted source material local:

1. Build a source manifest from a local private mirror.
2. Inventory PDF pages and detect text-layer vs scanned pages.
3. Extract layout-aware text locally.
4. Run local OCR only when needed.
5. Segment monster candidates.
6. Parse into the shared monster contract.
7. Validate and quarantine low-confidence records.
8. Load accepted records to Postgres.
9. Trigger dbt/app read-model refreshes.

The current files are scaffolding. Each asset returns metadata or synthetic placeholders
until extraction rules and the first field inventory are complete.

## Create a source manifest

Before extracting a new PDF, create a private source manifest:

```sh
uv run madtitan-pipelines source-manifest create
```

The command asks for the book title, ruleset, local PDF path, page range settings, and
preferred extraction methods. It writes a validated `SourceBook` manifest to
`SOURCE_MANIFEST_PATH`, or `data/source_manifests/` by default. That directory is
ignored by git because it can contain private local paths.

If `LOCAL_PDF_MIRROR` is set in `.env`, the manifest creator can accept either:

- an absolute PDF path, such as `/Users/you/Documents/bestiaries/book.pdf`
- a relative PDF path inside the mirror, such as `book.pdf`

The default preferred methods are:

- `pdf_text_layer`: read embedded/selectable PDF text first.
- `local_ocr`: render pages locally and run OCR when needed.

Other supported methods are:

- `llm_vision_text`: use an LLM vision pass for hard pages.
- `manual_transcription`: use human-entered text for fixtures or repairs.

If `llm_vision_text` is included in preferred methods, `allow_llm_vision` is set to
true automatically. Otherwise, the CLI asks whether LLM vision is allowed as a fallback.

Validate one manifest or the manifest directory:

```sh
uv run madtitan-pipelines source-manifest validate data/source_manifests
```

List registered manifests:

```sh
uv run madtitan-pipelines source-manifest list
```

The loader rejects duplicate `source_book_id` values and refuses to overwrite an
existing manifest during creation.

## Inspect PDF page inventory

After a source manifest exists, inspect the PDF page inventory before extraction:

```sh
uv run madtitan-pipelines page-inventory inspect data/source_manifests/behir-test-pdf.json
```

To include one line per page:

```sh
uv run madtitan-pipelines page-inventory inspect data/source_manifests/behir-test-pdf.json --show-pages
```

The page inventory step reads the PDF locally and records internal routing metadata:

- page number and PDF page label
- page dimensions in PDF points
- rotation
- text-layer status: `usable`, `low_text`, `empty`, or `unavailable`
- text character count, without storing the page text itself
- image count
- whether the page likely needs OCR, with reason codes
- recommended extraction methods for the page

If `page_start` and `page_end` are both `null`, the inventory scans the full PDF.
