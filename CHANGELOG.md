# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 2026-05-12
- **Created** `flows/ingest-metadata.yaml` — metadata-only pipeline (runs hourly), separated from audio downloads (Stage 6)
- **Created** `flows/download-audio.yaml` — audio download pipeline (runs every 6 hours), queries DB for un-downloaded episodes (Stage 6)
- **Created** `README.md` — project root README with architecture, quick start, schema docs (Stage 6)
- **Created** `dashboard/.dockerignore` — excludes `.env`, `__pycache__`, `.git` from Docker build context (Stage 6)
- **Fixed** Dashboard sidebar SQL injection — replaced f-string category/date filters with parameterized queries (Stage 4f)
- **Improved** `update_log` in pipeline flows — now populates `feeds_processed`, `episodes_inserted`, `download_success`, `download_failed` with actual counts (Stage 5)
- **Updated** `.gitignore` — added `__pycache__/`, `*.pyc`, `.DS_Store`, IDE configs

### 2026-05-11
- **Fixed** `docker-compose.yml` — removed broken `depends_on: kestra` from `pgdatabase`; added correct `depends_on: pgdatabase` to `kestra_postgres`
- **Replaced** Metabase dashboard with lightweight Streamlit dashboard (`dashboard/` directory)
- **Removed** `deploy/metabase_setup.sh` (no longer needed — dashboard is code-defined)
- **Updated** `deploy/README.md` to reflect Streamlit on port 8501 instead of Metabase on 3000
- **Updated** `.env.example` to remove Metabase env vars
- **Added** `CHANGELOG.md`
- **Created** `flows/init-schema.yaml` — centralised schema creation flow
- **Created** `flows/seed-feeds.yaml` — feed catalog seeding flow
