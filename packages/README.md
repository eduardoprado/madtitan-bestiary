# Packages

Shared contracts and helper packages used across extraction, dbt, API, and analytics.

Current scaffold:

- `contracts/python`: Pydantic draft models for parser output and validation.
- `contracts/schemas`: JSON Schema draft for language-agnostic validation.

## Fixture Validation

From the repo root, after `uv sync --all-packages` (see [README](../README.md#local-development)):

```sh
uv run madtitan-contracts validate samples
uv run madtitan-contracts validate samples/fixtures/srd/dire_wolf_2024_structure.json
```

Folders are scanned recursively for `*.json` files. A fixture file may contain either
one monster object or an array of monster objects.
