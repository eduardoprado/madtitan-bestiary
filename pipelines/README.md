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
