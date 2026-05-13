# 🎙️ Podcast Downloader Pipeline

An automated, end-to-end data engineering pipeline that discovers, ingests, and analyses podcast episodes from 48+ RSS feeds across 7 categories.

## What It Does

1. **Discovers** podcasts from a database-driven feed catalog (48 feeds, 7 categories)
2. **Fetches** RSS/XML feeds and extracts rich episode metadata (title, duration, publish date, category, keywords, etc.)
3. **Stores** structured data in PostgreSQL with upsert logic (no duplicates)
4. **Downloads** audio files (MP3) with retry logic and deduplication
5. **Visualises** everything in a Streamlit dashboard with 4 interactive tabs

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Kestra (Workflow Orchestrator) — :8089                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ ingest-      │  │ download-    │  │ init-schema /      │   │
│  │ metadata     │→ │ audio        │  │ seed-feeds         │   │
│  │ (hourly)     │  │ (every 6h)   │  │ (one-time setup)   │   │
│  └──────┬───────┘  └──────┬───────┘  └────────────────────┘   │
│         │                 │                                     │
│         ▼                 ▼                                     │
│  ┌─────────────────────────────┐   ┌────────────────────────┐  │
│  │  PostgreSQL — :5432         │   │  podcast_audio volume  │  │
│  │  podcast_feeds              │   │  (persisted MP3 files) │  │
│  │  podcast_metadata           │   └────────────────────────┘  │
│  │  podcast_downloads          │                                │
│  │  pipeline_run_log           │                                │
│  │  + 6 analytical views       │                                │
│  └─────────────┬───────────────┘                                │
│                │                                                │
│  ┌─────────────▼───────────────┐   ┌────────────────────────┐  │
│  │  Streamlit Dashboard — :8501│   │  pgAdmin — :8085       │  │
│  │  📊 Overview │ 🎙 Shows     │   │  (DB admin UI)         │  │
│  │  📅 Trends  │ 🔧 Health     │   └────────────────────────┘  │
│  └─────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- ~4 GB RAM (for all services)
- ~30 GB disk (for audio files over time)

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/pyth0nkod3r/podcast-downloader-pipeline.git
cd podcast-downloader-pipeline
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Postgres credentials
```

Generate the Kestra secrets file:

```bash
bash encode_env.bash
# This creates .env_encoded with base64-encoded SECRET_ prefixed vars
```

### 3. Start the stack

```bash
docker compose up -d
```

Wait ~30 seconds for all services to start. Then verify:

| Service | URL | Purpose |
|---------|-----|---------|
| Kestra | http://localhost:8089 | Workflow orchestrator |
| Streamlit | http://localhost:8501 | Analytics dashboard |
| pgAdmin | http://localhost:8085 | Database admin |
| PostgreSQL | localhost:5432 | Podcast data store |

### 4. Initialise the database

In the Kestra UI (http://localhost:8089):

1. Go to **Flows** → upload all YAML files from the `flows/` directory
2. Run **`init-schema`** — creates all tables and analytical views
3. Run **`seed-feeds`** — populates the feed catalog with 48 podcasts

### 5. Run the pipeline

- Run **`ingest-metadata`** manually for the first run, or wait for the hourly schedule
- Run **`download-audio`** manually, or wait for the 6-hour schedule

### 6. View the dashboard

Open http://localhost:8501 — the Podcast Pipeline Monitor shows:

- **📊 Overview** — KPIs, top shows, category breakdown, duration stats
- **🎙️ Shows** — per-feed deep dive with duration trends and episode tables
- **📅 Trends** — weekly volume, publishing heatmap, duration vs. description scatter
- **🔧 Pipeline Health** — download status, data quality scores, run logs

## Services

| Service | Image | Role |
|---------|-------|------|
| `pgdatabase` | postgres:18 | Stores podcast metadata, downloads, run logs |
| `kestra_postgres` | postgres:18 | Kestra's internal state database |
| `kestra` | kestra/kestra:v1.3.8 | Orchestrates the RSS → extract → load → download pipeline |
| `pgadmin` | dpage/pgadmin4:9.14.0 | Web-based PostgreSQL admin |
| `streamlit` | Custom (Python 3.11) | Interactive analytics dashboard |

## Kestra Flows

| Flow | Schedule | Purpose |
|------|----------|---------|
| `init-schema` | Manual (once) | Creates all tables and views |
| `seed-feeds` | Manual (once) | Populates the feed catalog |
| `ingest-metadata` | Every hour | Fetches RSS → extracts metadata → loads into Postgres |
| `download-audio` | Every 6 hours | Downloads MP3 files for episodes with audio URLs |

## Database Schema

### Tables
- **`podcast_feeds`** — Feed catalog (name, URL, category, active status)
- **`podcast_metadata`** — Episode data (title, duration, pub date, category, 19 columns)
- **`podcast_downloads`** — Audio download tracking (status, file path, timestamp)
- **`pipeline_run_log`** — Execution logs (start/end time, counts, errors)

### Analytical Views
- **`v_episodes_clean`** — Typed/parsed base view for all analytics
- **`v_feed_stats`** — One summary row per feed
- **`v_publishing_heatmap`** — Day × hour publishing pattern
- **`v_weekly_volume`** — Weekly episode counts by category
- **`v_download_health`** — Daily download status breakdown
- **`v_data_quality`** — Metadata completeness scores per feed

## Project Structure

```
podcast-downloader-pipeline/
├── dashboard/
│   ├── app.py                 # Streamlit dashboard (4 tabs, 15+ charts)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
├── flows/
│   ├── init-schema.yaml       # Table + view creation
│   ├── seed-feeds.yaml        # Feed catalog seeder
│   ├── ingest-metadata.yaml   # RSS fetch → extract → load metadata
│   └── download-audio.yaml    # Audio file downloader
├── deploy/
│   └── README.md              # Azure / Coolify deployment guide
├── docker-compose.yml
├── .env.example
├── CHANGELOG.md
└── README.md                  # ← You are here
```

## Deployment

For production deployment on Azure with Coolify, see [deploy/README.md](deploy/README.md).

## License

This project is for educational purposes.
