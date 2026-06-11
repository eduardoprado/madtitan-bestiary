# Warehouse

dbt project targeting Postgres schemas:

- `raw`: source metadata, page inventory, parser output, quarantine records.
- `core`: validated source-specific monster occurrence records and normalized detail.
- `mart`: dimensional/fact models for analytics.
- `app`: accepted-only read models, search tables, and facet metadata.

The SQL models are intentionally placeholders until the field inventory and first
parser fixtures define stable grain and columns.
