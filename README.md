# MadTitan Bestiary

A personal, end-to-end data platform that turns a library of D&D 5e bestiary PDFs into
a fast, richly-filterable monster search tool **and** a deep analytics workbench for a DM.

> **Status:** Planning / pre-implementation. This repo currently contains the
> architecture and design docs only — no application code yet.
> See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for the full design.

---

## What it does (when built)

1. **Ingests** raw bestiary PDFs (text-based *and* scanned) from private storage.
2. **Extracts** every monster into a strict, comprehensive structured schema using an
   LLM (text + vision), with validation and a quarantine workflow for bad records.
3. **Models** the data in a medallion lakehouse (bronze → silver → gold) with dbt.
4. **Serves** a private website for the DM: fuzzy name search, full-text search inside
   traits/actions, and a generic, metadata-driven faceted filter system
   (CR, type, subtype, size, alignment, damage dealt/resisted/immune, conditions,
   senses, movement, spellcaster, legendary, environment, source, AC/HP ranges, …).
5. **Powers** in-depth analytical reports (e.g. *average damage/round vs CR with an
   over/under-tuned baseline*, AC/HP vs CR, distributions, damage-type landscape,
   action-economy analysis).

## Design priorities

- **~$0/month.** Free tiers only, end to end.
- **Private data, public code.** All code can live in a public GitHub repo; the
  copyrighted book data **never** enters the repo (see `.gitignore` + the data policy
  in `ARCHITECTURE.md`).
- **State-of-the-art, portfolio-grade stack** across data engineering, analytics
  engineering, and full-stack web.
- **Extensible.** Architected to later add spells, monster creation, and an encounter
  simulator as new domains.

## High-level systems

| # | System | Core tech |
|---|--------|-----------|
| 1 | Ingestion & extraction | Python · PyMuPDF · Google Gemini (text + vision) · Pydantic |
| 2 | Lakehouse / warehouse | Databricks Free Edition (Delta + Unity Catalog) · dbt |
| 3 | Serving + API | Postgres (Supabase/Neon) · FastAPI |
| 4 | Web + analytics | Next.js (TS) · Databricks notebooks / dashboards |
| — | Security | Cloudflare Access (Zero Trust) |
| — | Infra / CI | Terraform · GitHub Actions |

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for diagrams, the data model, the data
flow around Databricks' outbound-network limitation, the full scope, and the phased
roadmap.

## Repository layout (planned)

```
madtitan-bestiary/
  pipelines/      # extract (PyMuPDF+Gemini+Pydantic), load (-> Databricks), export (Databricks -> Postgres)
  warehouse/      # dbt project (staging -> dim/fact -> marts), tests, docs
  analytics/      # notebooks + reports
  api/            # FastAPI service
  web/            # Next.js + Tailwind + shadcn/ui
  infra/          # Terraform (R2, Cloudflare Access, ...)
  .github/        # CI: dbt tests, lint, deploy
  docs/           # additional design docs
```

## Legal / data note

D&D **rules and statistics** are generally not copyrightable, and the **5e SRD** is
licensed under **CC-BY-4.0**. However, the **lore/flavor text and non-SRD creatures**
in commercial bestiaries are copyrighted. This project is **personal, single-user, and
private**: the underlying book data is never published, and only **SRD/CC-BY content**
is ever used as shareable sample/test fixtures in this repo.
