# MadTitan Bestiary

A personal, end-to-end data platform that turns a private library of D&D 5e bestiary
PDFs into a fast, richly-filterable monster search tool and a deep analytics
workbench for a DM.

> **Status:** Phase 0 scaffold. The repo now contains the architecture docs plus
> starter workspaces for pipelines, warehouse models, analytics, web, shared contracts,
> infrastructure notes, sample fixtures, and CI guardrails.
> See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for the full design.

---

## What it does when built

1. **Ingests** raw bestiary PDFs from private storage and a local mirror.
2. **Extracts** every monster into a strict, comprehensive structured schema using a
   private-first pipeline: local PDF parsing, local OCR for scanned pages, validation,
   and quarantine for uncertain records.
3. **Models** the data inside Postgres using clear raw, core, mart, and app-facing
   schemas.
4. **Serves** a private website for the DM: fuzzy name search, full-text search inside
   traits/actions, and a generic, metadata-driven faceted filter system.
5. **Powers** in-depth analytical reports, including damage/round vs CR, AC/HP vs CR,
   distributions, damage-type landscape, and action-economy analysis.

## Design priorities

- **Low cost.** Prefer free tiers and local compute. Keep the v1 stack small enough to
  run for roughly $0/month, with room for a small storage/database upgrade later.
- **Private data, public code.** All code can live in a public GitHub repo; copyrighted
  book data never enters the repo or any public surface.
- **Private-first extraction.** Raw PDFs, extracted text, and copyrighted lore stay
  under the owner's control. Hosted AI extraction is not part of v1.
- **Portfolio-grade architecture.** Show a real data platform: orchestration, data
  quality, lineage, typed contracts, analytics marts, search UX, and security.
- **Extensible.** Architected to later add spells, monster creation, and an encounter
  simulator as new domains.

## High-level systems

| #   | System                        | Core tech                                                  |
| --- | ----------------------------- | ---------------------------------------------------------- |
| 1   | Ingestion and extraction      | Python, Dagster OSS, Docling/PyMuPDF, local OCR, Pydantic  |
| 2   | Warehouse and search database | Postgres, dbt Core, `pg_trgm`, full-text search, JSONB     |
| 3   | Private web app and API       | Next.js, TypeScript, Auth.js allowlist                     |
| 4   | Analytics workbench           | Python notebooks, SQL marts, generated HTML reports        |
| -   | Storage and governance        | Cloudflare R2, local mirror, secrets management            |
| -   | Infra and CI                  | Terraform where useful, GitHub Actions, synthetic fixtures |

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for diagrams, data flow, the provisional
modeling approach, security policy, and phased roadmap.

## Repository layout

```text
madtitan-bestiary/
  pipelines/      # Python/Dagster assets for ingest, extract, validate, load
  warehouse/      # dbt project targeting Postgres schemas and marts
  analytics/      # notebooks + generated reports
  web/            # Next.js + TypeScript app, API routes, Auth.js allowlist
  packages/       # shared schema/contracts and typed DB helpers
  infra/          # Terraform/config for R2, database, deployment, secrets docs
  samples/        # SRD/CC-BY or synthetic fixtures only
  .github/        # CI: tests, lint, dbt checks, docs checks
  docs/           # local setup and data/secrets policy
```

## Local development

### Prerequisites

- **Python 3.11+** (required by the Python workspaces)
- **[uv](https://docs.astral.sh/uv/)** — package manager for this monorepo
- **Docker Desktop** — for local Postgres (`docker compose`)

### Python setup

This repo uses a **uv workspace** spanning `pipelines/` and `packages/contracts/python/`.
Run these from the **repo root**:

```sh
# Install uv (macOS/Linux) — skip if already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create .venv and install all workspace packages
uv sync --all-packages

# Optional: dev tools (pytest, ruff) for local testing/linting
uv sync --all-packages --extra dev
```

`uv sync` reads `pyproject.toml` and `uv.lock`, installs dependencies into `.venv`, and
installs the workspace packages. Use `uv run ...` to run commands in that environment
without manually activating the venv.

### Validate fixture JSON

Monster fixtures under `samples/` are validated against the shared Pydantic contract in
`packages/contracts/python/`:

```sh
# All JSON files under samples/ (recursive)
uv run madtitan-contracts validate samples

# One file
uv run madtitan-contracts validate samples/fixtures/srd/dire_wolf_2024_structure.json
```

### Run contract tests

```sh
uv run pytest packages/contracts/python/tests
```

Requires `uv sync --all-packages --extra dev`.

### Start Postgres

```sh
docker compose up -d postgres
```

Copy `.env.example` to `.env` and adjust values before running services. Full setup
for Dagster, dbt, and the web app is in [docs/LOCAL_SETUP.md](./docs/LOCAL_SETUP.md).

## Local scaffold entry points

- **Setup:** [docs/LOCAL_SETUP.md](./docs/LOCAL_SETUP.md)
- **Secrets/data rules:** [docs/SECRETS_AND_DATA.md](./docs/SECRETS_AND_DATA.md)
- **Extraction pipeline:** [docs/EXTRACTION_PIPELINE.md](./docs/EXTRACTION_PIPELINE.md)
- **Postgres:** `docker-compose.yml`
- **Dagster pipeline:** `pipelines/`
- **dbt warehouse:** `warehouse/`
- **Next.js app:** `web/`
- **Shared contracts:** `packages/contracts/`
- **Field inventory:** [docs/FIELD_INVENTORY.md](./docs/FIELD_INVENTORY.md)

## Legal / data note

D&D rules and statistics are generally treated differently from expressive lore, and
the 5e SRD is licensed under CC-BY-4.0. Commercial bestiary lore, flavor text,
artwork, and non-SRD creatures may be copyrighted.

This project is personal, single-user, and private. The underlying book data is never
published. Only SRD/CC-BY content or synthetic fixtures are allowed in the public repo,
tests, screenshots, demos, and portfolio material.
