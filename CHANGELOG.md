# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 2026-05-11
- **Fixed** `docker-compose.yml` — removed broken `depends_on: kestra` from `pgdatabase`; added correct `depends_on: pgdatabase` to `kestra_postgres`
- **Replaced** Metabase dashboard with lightweight Streamlit dashboard (`dashboard/` directory)
- **Removed** `deploy/metabase_setup.sh` (no longer needed — dashboard is code-defined)
- **Updated** `deploy/README.md` to reflect Streamlit on port 8501 instead of Metabase on 3000
- **Updated** `.env.example` to remove Metabase env vars
- **Added** `CHANGELOG.md`
- **Created** `flows/init-schema.yaml` — centralised schema creation flow
- **Created** `flows/seed-feeds.yaml` — feed catalog seeding flow
