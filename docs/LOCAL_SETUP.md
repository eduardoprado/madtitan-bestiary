# Local Setup

This repo is scaffolded for a private-first local workflow. Raw PDFs, extracted page
text, exports, and secrets should live outside Git.

## 1. Configure environment

Copy `.env.example` to `.env` and update:

- `DATABASE_URL`
- `LOCAL_PDF_MIRROR`
- optional R2 credentials
- `AUTH_ALLOWED_EMAILS`

## 2. Start Postgres

```sh
docker compose up -d postgres
```

The default local database is `madtitan_bestiary`.

## 3. Python/Dagster workspace

The pipeline scaffold lives in `pipelines/`. It defines placeholder Dagster assets for
the Phase 0/1 flow:

- source manifest
- page inventory
- extraction candidates
- parser validation
- Postgres/dbt refresh boundaries

## 4. dbt workspace

The dbt scaffold lives in `warehouse/`. Use `warehouse/profiles.yml.example` as the
shape for your local dbt profile, but keep the real `profiles.yml` out of Git.

## 5. Web workspace

The Next.js scaffold lives in `web/`. It currently exposes a health endpoint and shell
pages for search/detail work.
