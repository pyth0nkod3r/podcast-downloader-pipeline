# Podcast Pipeline — Staged Implementation Plan
> Generated: May 11, 2026  
> Project: `podcast-downloader-pipeline`  
> Skill level: Beginner-friendly  

---

## How to use this document

Each stage builds directly on the one before it. Every task is written as a clear,
atomic action — something you or an AI assistant can pick up, complete, and tick off
without needing to read the whole document first. Stages are designed to leave the
project in a **working state** at the end, so you can stop after any stage and still
have something that runs.

**Legend**
- 📝 Write / edit code or config
- 🗄️ Database / SQL work  
- 🔄 Kestra flow work  
- 🧪 Test / verify  
- 📊 Dashboard work  

---

## The Questions We Want This Data to Answer

These are the analytical questions that drive every design decision in the plan.
By the end of all stages, the dashboard and database should be able to answer all of them.

### About individual episodes
1. Which episode from any feed is the longest ever recorded?
2. Which episode has the shortest description? Does description length correlate with episode quality or popularity?
3. On which day of the week are most episodes published?
4. At what hour of the day do most creators publish?
5. Are episodes getting longer or shorter over time for a given show?
6. How many episodes in the catalog have no downloadable audio URL?
7. Which episodes have been in the feed the longest without being downloaded?
8. What fraction of episodes are marked "explicit"?

### About shows / feeds
9. Which podcast publishes the most episodes per month?
10. Which podcast has the most consistent publishing schedule (least variance between episodes)?
11. Which show has the highest average episode duration?
12. Which shows are still active (published in the last 30 days) vs. dormant?
13. How many total hours of audio content exist across all feeds?
14. Which category of podcast (tech, science, business, etc.) produces the most content per week?
15. Which shows share the same creator across multiple feeds?

### About the pipeline's health
16. What is the overall audio download success rate?
17. Which feed consistently produces the most download failures?
18. How many new episodes were ingested in the last 24 hours?
19. Are there duplicate GUIDs appearing across different feeds?
20. What percentage of episodes have all key metadata fields filled in (title, duration, audio URL, pubDate)?
21. How long does each pipeline run take from start to finish?
22. Which pipeline runs failed, and at which task did they fail?

### About trends over time
23. Is the total volume of new podcast episodes growing, shrinking, or flat week over week?
24. Which category is growing fastest in episode output?
25. Is average episode duration trending up or down across the whole catalog over the past year?
26. Are descriptions getting more or less detailed (word count) over time?

---

## RSS Feed Catalog

These feeds span multiple categories and collectively expose thousands of episodes.
They are the raw material for the whole project.
Add them to a `podcast_feeds` table in Stage 1.

### Technology
| Feed Name | RSS URL |
|---|---|
| Syntax.fm | `https://feed.syntax.fm/rss` |
| The Changelog | `https://changelog.com/podcast/feed` |
| Software Engineering Daily | `https://softwareengineeringdaily.com/feed/podcast/` |
| Darknet Diaries | `https://feeds.megaphone.fm/darknetdiaries` |
| Command Line Heroes | `https://feeds.pacific-content.com/commandlineheroes` |
| Hanselminutes | `https://feeds.simplecast.com/gvtxUiIf` |
| The Stack Overflow Podcast | `https://feeds.simplecast.com/XA_851k3` |
| JS Party | `https://changelog.com/jsparty/feed` |
| Go Time | `https://changelog.com/gotime/feed` |
| Practical AI | `https://changelog.com/practicalai/feed` |
| Lex Fridman Podcast | `https://lexfridman.com/feed/podcast/` |
| CoRecursive | `https://corecursive.com/feed` |
| DevOps Paradox | `https://www.devopsparadox.com/feed/podcast/` |
| Ship It! | `https://changelog.com/shipit/feed` |
| The Bike Shed | `https://feeds.fireside.fm/bikeshed/rss` |
| Developer Tea | `https://feeds.simplecast.com/dCXMIpJz` |

### Science
| Feed Name | RSS URL |
|---|---|
| Radiolab | `https://feeds.simplecast.com/EmVW7VGp` |
| Science Vs | `https://feeds.megaphone.fm/sciencevs` |
| Huberman Lab | `https://feeds.megaphone.fm/hubermanlab` |
| Stuff You Should Know | `https://omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/A91018A4-EA4F-4130-BF55-AE270180C671/44710ECC-10BB-48D1-93C7-AE270180C67F/podcast.rss` |
| Hidden Brain | `https://feeds.npr.org/510308/podcast.xml` |
| Freakonomics Radio | `https://feeds.simplecast.com/Y8lFbOT4` |
| In Our Time: Science | `https://feeds.feedburner.com/b0d040` |
| The Skeptics Guide to the Universe | `https://feed.theskepticsguide.org/feed/sgu` |
| Crash Course Pods: The Universe | `https://feeds.megaphone.fm/crashcoursepods` |
| Short Wave (NPR) | `https://feeds.npr.org/510351/podcast.xml` |

### Business & Finance
| Feed Name | RSS URL |
|---|---|
| How I Built This | `https://feeds.npr.org/510313/podcast.xml` |
| Masters of Scale | `https://rss.art19.com/masters-of-scale` |
| Planet Money | `https://feeds.npr.org/510289/podcast.xml` |
| The Tim Ferriss Show | `https://rss.art19.com/tim-ferriss-show` |
| My First Million | `https://feeds.megaphone.fm/myfirstmillion` |
| Acquired | `https://feeds.simplecast.com/lt2IQZL6` |
| Invest Like the Best | `https://feeds.megaphone.fm/investlikethebest` |
| The Knowledge Project | `https://feeds.simplecast.com/lG6dOVHY` |
| WorkLife with Adam Grant | `https://feeds.feedburner.com/WorklifeWithAdamGrant` |
| Founders | `https://feeds.simplecast.com/h0lGRWvg` |

### True Crime & Storytelling
| Feed Name | RSS URL |
|---|---|
| Serial | `https://feeds.serialpodcast.org/serialpodcast` |
| My Favorite Murder | `https://feeds.simplecast.com/Xe8OTjoW` |
| Criminal | `https://feeds.simplecast.com/4T3_oCr2` |
| This American Life | `https://www.thisamericanlife.org/podcast/rss.xml` |
| Casefile True Crime | `https://feeds.audioboom.com/posts/7898936-casefile-true-crime/feed.rss` |
| Stuff They Don't Want You To Know | `https://feeds.simplecast.com/HjMIFFlx` |
| Snap Judgment | `https://feeds.feedburner.com/snapjudgment-hd` |

### Health & Wellness
| Feed Name | RSS URL |
|---|---|
| Ten Percent Happier | `https://feeds.simplecast.com/lRTUgHMO` |
| The Doctor's Farmacy | `https://feeds.megaphone.fm/thedoctorsfarmacy` |
| On Being with Krista Tippett | `https://feeds.feedburner.com/OnBeing` |
| Feel Better Live More | `https://feeds.acast.com/public/shows/feel-better-live-more-with-dr-rangan-chatterjee` |
| The Model Health Show | `https://feeds.simplecast.com/nqZCKqlS` |

### News & Politics
| Feed Name | RSS URL |
|---|---|
| The Daily (NYT) | `https://feeds.simplecast.com/54nAGcIl` |
| Up First (NPR) | `https://feeds.npr.org/510318/podcast.xml` |
| The Indicator from Planet Money | `https://feeds.npr.org/510325/podcast.xml` |
| Axios Today | `https://feeds.simplecast.com/l8BF1NN7` |
| Marketplace Morning Report | `https://feeds.marketplace.org/marketplace-morning-report` |

### Comedy & Culture
| Feed Name | RSS URL |
|---|---|
| Conan O'Brien Needs a Friend | `https://feeds.simplecast.com/dHoohVNH` |
| SmartLess | `https://feeds.simplecast.com/pHMEHy5M` |
| My Brother, My Brother and Me | `https://feeds.maximumfun.org/my-brother-my-brother-and-me/feed.xml` |
| Wait Wait Don't Tell Me | `https://feeds.npr.org/344098539/podcast.xml` |
| Stuff You Missed in History Class | `https://feeds.megaphone.fm/stuffyoumissedinhistoryclass` |
| Pop Culture Happy Hour | `https://feeds.npr.org/510282/podcast.xml` |

### Data, AI & Learning
| Feed Name | RSS URL |
|---|---|
| Data Skeptic | `https://dataskeptic.com/feed.rss` |
| Super Data Science | `https://feeds.sounder.fm/show/super-data-science-podcast` |
| Towards Data Science | `https://towardsdatascience.com/feed` |
| The TWIML AI Podcast | `https://feeds.megaphone.fm/MLN2155636147` |
| DataFramed | `https://feeds.buzzsprout.com/394933.rss` |
| Ologies with Alie Ward | `https://feeds.simplecast.com/JRFZ3dAK` |

---

## Stage 0 — Fix Existing Bugs Before Adding Anything New
> **Goal:** Make sure the current pipeline runs cleanly end-to-end.  
> **Why first:** There's no point building on a cracked foundation.

### Tasks
- [ ] 📝 In `docker-compose.yml`, fix the `depends_on` order: `pgdatabase` should NOT depend on `kestra`. Instead, `kestra` (the service) depends on `kestra_postgres`. The `streamlit` service depends on `pgdatabase`. Remove the broken `depends_on: kestra` line from the `pgdatabase` block.
- [ ] 📝 In `flows/rss-podcast-poc.yaml`, fix the yellow taxi condition — it uses `{{ render(inputs.taxi == 'yellow') }}` which is wrong syntax. The correct form is `"{{inputs.taxi == 'yellow'}}"`. *(Note: the taxi flow is in the practice folder and won't affect the podcast pipeline, but fixing it is good hygiene.)*
- [ ] 📝 In `flows/rss-podcast-poc.yaml`, the `load_staging_table` task references `outputs.extract_podcasts.outputFiles['podcast_data.csv']` wrapped in `render()` — double-check this resolves correctly by running the flow once manually with `commit_your_code` and watching the Kestra logs.
- [ ] 🧪 Run the pipeline once for each of the 3 existing feeds manually from the Kestra UI. Confirm rows appear in `podcast_metadata` and `podcast_downloads` using pgAdmin.
- [ ] 🧪 Open the Streamlit dashboard at `:8501` and verify all 4 charts render without error. Note which ones show "No data available" — those should be populated after the pipeline run above.
- [ ] 📝 Create a `CHANGELOG.md` file in the project root. Log every change you make from this point forward with a date and a one-line description. This is a good engineering habit.

---

## Stage 1 — Expand the Feed Catalog
> **Goal:** Replace the 3 hardcoded feed names with a database-driven catalog of 50+ feeds.  
> **Why:** More feeds = more rows = more interesting data. This is the single biggest lever for data volume.

### 1a — Create the feeds table in Postgres

- [ ] 🗄️ In Kestra, create a new flow called `init-schema.yaml` in the `flows/` folder. This flow will be responsible for creating all database tables. It should only be run once manually (no trigger).
- [ ] 🗄️ In `init-schema.yaml`, add a task that creates the `podcast_feeds` table with these columns:
  ```sql
  CREATE TABLE IF NOT EXISTS podcast_feeds (
    feed_id     SERIAL PRIMARY KEY,
    feed_name   TEXT NOT NULL,
    rss_url     TEXT NOT NULL UNIQUE,
    category    TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    added_at    TIMESTAMP DEFAULT NOW(),
    last_fetched_at TIMESTAMP
  );
  ```
- [ ] 🗄️ In `init-schema.yaml`, also move the `CREATE TABLE IF NOT EXISTS podcast_metadata` and `CREATE TABLE IF NOT EXISTS podcast_downloads` statements here from `rss-podcast-poc.yaml`. Tables should be created once by a schema flow, not every time the pipeline runs.
- [ ] 🧪 Run `init-schema.yaml` manually from Kestra UI. Verify all 3 tables exist in pgAdmin.

### 1b — Seed the feeds catalog

- [ ] 📝 Create a file called `flows/seed-feeds.yaml`. This is a one-time Kestra flow with a Python script task that inserts the RSS feed list into `podcast_feeds`.
- [ ] 📝 In the Python script inside `seed-feeds.yaml`, define the feed list as a Python list of dicts with keys `feed_name`, `rss_url`, and `category`. Use the RSS Feed Catalog table from this document as your source — add at least 30 feeds across at least 4 categories.
- [ ] 📝 Use `psycopg2` (already available in Kestra's Python environment) to connect to the database and `INSERT ... ON CONFLICT (rss_url) DO NOTHING` so the seed is safe to re-run.
- [ ] 🧪 Run `seed-feeds.yaml` manually. In pgAdmin, run `SELECT category, COUNT(*) FROM podcast_feeds GROUP BY category ORDER BY 2 DESC;` and confirm all your feeds appear.

### 1c — Update the main pipeline to loop over the catalog

- [ ] 📝 In `rss-podcast-poc.yaml`, replace the hardcoded `inputs` section (the SELECT dropdown with 3 values) with a Python task called `fetch_active_feeds` that queries `SELECT feed_id, feed_name, rss_url, category FROM podcast_feeds WHERE is_active = TRUE` and returns the results as a JSON file.
- [ ] 📝 Add a `ForEach` loop task in Kestra that iterates over the feeds returned by `fetch_active_feeds` and calls a sub-flow (or repeats the extraction tasks) for each feed. 
  > **Beginner note:** Kestra's `io.kestra.plugin.core.flow.ForEach` lets you loop over a list and run tasks for each item. The [Kestra docs on ForEach](https://kestra.io/docs/workflow-components/tasks/flow/for-each) have a simple example. You pass `{{ taskrun.value }}` to get the current item in the loop.
- [ ] 📝 After each feed is successfully fetched, add a task that runs `UPDATE podcast_feeds SET last_fetched_at = NOW() WHERE rss_url = '...'` so you can track when each feed was last processed.
- [ ] 🧪 Trigger the updated pipeline manually. Check `podcast_metadata` — you should now see rows from multiple different sources. Run `SELECT source, COUNT(*) FROM podcast_metadata GROUP BY source ORDER BY 2 DESC;` in pgAdmin.

---

## Stage 2 — Enrich the Schema
> **Goal:** Store richer, properly typed data so we can answer the analytical questions.  
> **Why:** Raw strings can't be aggregated or charted meaningfully. Parsed fields can.

### 2a — Add new columns to `podcast_metadata`

- [ ] 🗄️ In `init-schema.yaml`, update the `podcast_metadata` CREATE TABLE statement to include the new columns below. Since you may have already run the schema flow, also add `ALTER TABLE` statements that add each column only if it doesn't already exist (use `IF NOT EXISTS` which is supported in PostgreSQL 9.6+):
  ```sql
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS pub_date         TIMESTAMP;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS episode_number   INTEGER;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS season_number    INTEGER;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS category         TEXT;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS keywords         TEXT;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS description_word_count INTEGER;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS audio_file_size_bytes  BIGINT;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS explicit         BOOLEAN;
  ALTER TABLE podcast_metadata ADD COLUMN IF NOT EXISTS image_url        TEXT;
  ```
- [ ] 🧪 Run the updated `init-schema.yaml`. Verify in pgAdmin that `podcast_metadata` now has all the new columns (they'll all be NULL for existing rows — that's fine for now).

### 2b — Parse the new fields in the extraction script

- [ ] 📝 In the `extract_podcasts` Python script inside `rss-podcast-poc.yaml`, add helper functions to parse each new field. Below are the helpers to add — copy them into the `#---helpers---` section:

  ```python
  def parse_duration(duration_str):
      """Converts itunes:duration to total seconds.
      Handles formats: '3600', '1:00:00', '60:00'
      """
      if not duration_str:
          return None
      try:
          parts = str(duration_str).strip().split(':')
          if len(parts) == 1:
              return int(parts[0])
          elif len(parts) == 2:
              return int(parts[0]) * 60 + int(parts[1])
          elif len(parts) == 3:
              return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
      except (ValueError, AttributeError):
          return None

  def parse_pub_date(date_str):
      """Parses RSS pubDate strings into ISO format.
      RSS dates look like: 'Mon, 10 May 2026 08:00:00 +0000'
      """
      if not date_str:
          return None
      from email.utils import parsedate_to_datetime
      try:
          return parsedate_to_datetime(str(date_str)).isoformat()
      except Exception:
          return None

  def word_count(text):
      """Counts words in a string, handling None safely."""
      if not text:
          return 0
      import re
      return len(re.findall(r'\w+', str(text)))

  def parse_explicit(explicit_str):
      """Converts itunes:explicit to a boolean."""
      if not explicit_str:
          return False
      return str(explicit_str).strip().lower() in ('yes', 'true', '1', 'explicit')

  def parse_file_size(item):
      """Extracts file size in bytes from the enclosure tag."""
      enclosure = item.get('enclosure', {})
      if isinstance(enclosure, dict):
          try:
              return int(enclosure.get('@length') or enclosure.get('length') or 0) or None
          except (ValueError, TypeError):
              return None
      return None
  ```

- [ ] 📝 Update the `result` list comprehension in the extraction script to populate all new fields using the helpers above:
  ```python
  result = [
    {
      "title":                  item.get("title"),
      "link":                   item.get("link"),
      "description":            item.get("description"),
      "duration":               item.get("itunes:duration"),       # keep raw
      "duration_seconds":       parse_duration(item.get("itunes:duration")),
      "creator":                extract_creator(item),
      "pubDate":                item.get("pubDate"),               # keep raw
      "pub_date":               parse_pub_date(item.get("pubDate")),
      "guid":                   extract_guid(item.get("guid")),
      "audio_url":              extract_audio_url(item),
      "source":                 source,
      "episode_number":         item.get("itunes:episode"),
      "season_number":          item.get("itunes:season"),
      "category":               item.get("itunes:category") or feed_category,
      "keywords":               item.get("itunes:keywords"),
      "description_word_count": word_count(item.get("description")),
      "audio_file_size_bytes":  parse_file_size(item),
      "explicit":               parse_explicit(item.get("itunes:explicit")),
      "image_url":              (item.get("itunes:image") or {}).get("@href"),
    }
    for item in items
  ]
  ```
  > **Beginner note:** `feed_category` should be passed into the script from the feed catalog (the `category` column you stored in `podcast_feeds`). When Kestra calls the script via `ForEach`, pass the category as a template variable.

- [ ] 📝 Update `podcast_staging` DDL in `init-schema.yaml` to include all the new columns so `CopyIn` doesn't fail.
- [ ] 📝 Update the `MERGE INTO podcast_metadata` SQL in the flow to include all new columns in both the `INSERT` columns list and the `VALUES` list.
- [ ] 🧪 Re-run the pipeline for 2–3 feeds. In pgAdmin, run:
  ```sql
  SELECT title, duration_seconds, pub_date, description_word_count, explicit
  FROM podcast_metadata
  WHERE duration_seconds IS NOT NULL
  ORDER BY duration_seconds DESC
  LIMIT 10;
  ```
  Verify you get real numbers back.

---

## Stage 3 — Add an Analytics Layer (SQL Views)
> **Goal:** Pre-compute the answers to the analytical questions as database views so the dashboard can query them simply.  
> **Why:** Views keep the dashboard code clean and make queries fast. Think of a view as a saved query with a name.

### 3a — Create analytical views

- [ ] 🗄️ In `init-schema.yaml`, add a new section of tasks that create the following views. Each one is a `CREATE OR REPLACE VIEW` statement:

  **View 1: `v_episodes_clean`** — a clean, typed version of the raw metadata table used as the base for all other views:
  ```sql
  CREATE OR REPLACE VIEW v_episodes_clean AS
  SELECT
    guid,
    title,
    source,
    category,
    creator,
    pub_date,
    DATE_TRUNC('day',  pub_date)  AS pub_day,
    DATE_TRUNC('week', pub_date)  AS pub_week,
    DATE_TRUNC('month',pub_date)  AS pub_month,
    EXTRACT(DOW  FROM pub_date)   AS day_of_week,   -- 0=Sunday, 6=Saturday
    EXTRACT(HOUR FROM pub_date)   AS hour_of_day,
    duration_seconds,
    ROUND(duration_seconds / 60.0, 1) AS duration_minutes,
    description_word_count,
    explicit,
    audio_url IS NOT NULL         AS has_audio,
    audio_file_size_bytes,
    keywords,
    image_url,
    created_at
  FROM podcast_metadata
  WHERE pub_date IS NOT NULL;
  ```

  **View 2: `v_feed_stats`** — one summary row per feed:
  ```sql
  CREATE OR REPLACE VIEW v_feed_stats AS
  SELECT
    source,
    category,
    COUNT(*)                              AS total_episodes,
    ROUND(AVG(duration_seconds)/60.0, 1) AS avg_duration_minutes,
    MAX(pub_date)                         AS latest_episode_date,
    MIN(pub_date)                         AS oldest_episode_date,
    ROUND(AVG(description_word_count),0)  AS avg_description_words,
    SUM(CASE WHEN explicit THEN 1 ELSE 0 END) AS explicit_episode_count,
    SUM(CASE WHEN audio_url IS NOT NULL THEN 1 ELSE 0 END) AS episodes_with_audio,
    NOW() - MAX(pub_date)                 AS days_since_last_episode
  FROM v_episodes_clean
  GROUP BY source, category;
  ```

  **View 3: `v_publishing_heatmap`** — counts by day-of-week and hour for the heatmap chart:
  ```sql
  CREATE OR REPLACE VIEW v_publishing_heatmap AS
  SELECT
    day_of_week,
    hour_of_day,
    COUNT(*) AS episode_count
  FROM v_episodes_clean
  GROUP BY day_of_week, hour_of_day;
  ```

  **View 4: `v_weekly_volume`** — episode counts per week for the trend chart:
  ```sql
  CREATE OR REPLACE VIEW v_weekly_volume AS
  SELECT
    pub_week,
    category,
    COUNT(*) AS episodes_published
  FROM v_episodes_clean
  GROUP BY pub_week, category
  ORDER BY pub_week;
  ```

  **View 5: `v_download_health`** — pipeline health summary:
  ```sql
  CREATE OR REPLACE VIEW v_download_health AS
  SELECT
    DATE_TRUNC('day', downloaded_at) AS day,
    status,
    COUNT(*) AS count
  FROM podcast_downloads
  GROUP BY 1, 2
  ORDER BY 1 DESC;
  ```

  **View 6: `v_data_quality`** — one row per feed showing completeness:
  ```sql
  CREATE OR REPLACE VIEW v_data_quality AS
  SELECT
    source,
    COUNT(*)                                                     AS total,
    ROUND(100.0 * SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END)           / COUNT(*), 1) AS pct_has_title,
    ROUND(100.0 * SUM(CASE WHEN audio_url IS NOT NULL THEN 1 ELSE 0 END)       / COUNT(*), 1) AS pct_has_audio_url,
    ROUND(100.0 * SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END)/ COUNT(*), 1) AS pct_has_duration,
    ROUND(100.0 * SUM(CASE WHEN pub_date IS NOT NULL THEN 1 ELSE 0 END)        / COUNT(*), 1) AS pct_has_pub_date,
    ROUND(100.0 * SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END)        / COUNT(*), 1) AS pct_has_category
  FROM podcast_metadata
  GROUP BY source
  ORDER BY total DESC;
  ```

- [ ] 🧪 After running `init-schema.yaml` with these new tasks, open pgAdmin and run a SELECT on each view. Confirm they return rows and the numbers look sensible.

---

## Stage 4 — Rebuild the Dashboard
> **Goal:** Replace the 4 basic charts with a full set of visualizations that answer the analytical questions.  
> **Why:** The data is now rich enough to support real insight. The dashboard is where all the work becomes visible.

### 4a — Restructure the Streamlit app layout

- [ ] 📝 Open `dashboard/app.py`. Replace the single page layout with a **tabbed layout** using `st.tabs()`. Create 4 tabs:
  - `📊 Overview` — headline metrics and top-line charts
  - `🎙️ Shows` — per-feed deep dives
  - `📅 Trends` — time-series and heatmaps
  - `🔧 Pipeline Health` — download status and data quality

  ```python
  tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎙️ Shows", "📅 Trends", "🔧 Pipeline Health"])
  ```

### 4b — Overview tab

- [ ] 📊 Add 5 top-level KPI metric cards in a row:
  - Total Episodes in Catalog
  - Total Shows / Feeds
  - Total Hours of Audio (`SUM(duration_seconds) / 3600` from `v_episodes_clean`)
  - Episodes Added (Last 7 Days)
  - Overall Download Success Rate
- [ ] 📊 Add a **bar chart** — "Top 15 Shows by Episode Count" (from `v_feed_stats`, sorted by `total_episodes` descending). Use a horizontal bar (`orientation='h'`) so long show names fit.
- [ ] 📊 Add a **pie/donut chart** — "Episodes by Category" (group `v_feed_stats` by `category`, sum `total_episodes`).
- [ ] 📊 Add a **bar chart** — "Average Episode Duration by Category" (from `v_feed_stats`, one bar per category, height = `avg_duration_minutes`).

### 4c — Shows tab

- [ ] 📊 Add a **dropdown selector** (`st.selectbox`) that lists all feed names from `podcast_feeds`. When a feed is selected, the rest of the tab updates.
- [ ] 📊 Below the selector, show a **stats row** for the selected feed: total episodes, avg duration, latest episode date, explicit episode count.
- [ ] 📊 Add a **line chart** — "Episode Duration Over Time" for the selected feed (x = `pub_date`, y = `duration_minutes` from `v_episodes_clean WHERE source = selected`).
- [ ] 📊 Add a **bar chart** — "Episodes Published Per Month" for the selected feed.
- [ ] 📊 Add a **data table** — the 20 most recent episodes for the selected feed (title, pub_date, duration_minutes, description_word_count).

### 4d — Trends tab

- [ ] 📊 Add a **line chart** — "Weekly Episode Volume by Category" (from `v_weekly_volume`). Use one line per category, different colors.
- [ ] 📊 Add a **heatmap** — "When Do Creators Publish?" using `v_publishing_heatmap`. 
  > **Beginner note:** Plotly doesn't have a built-in heatmap for this, but you can use `px.density_heatmap` or reshape the data with pandas `pivot_table` and then use `go.Heatmap`. The x-axis should be hours 0–23, y-axis should be days (Sunday–Saturday). Cell color = episode count.
- [ ] 📊 Add a **scatter plot** — "Episode Duration vs. Description Word Count" (from `v_episodes_clean`). Each dot is one episode, colored by category. This helps answer whether longer descriptions correlate with longer episodes.
- [ ] 📊 Add a **line chart** — "Average Episode Duration Trend" (weekly average of `duration_minutes` across all feeds, from `v_weekly_volume` joined back to `v_episodes_clean`).

### 4e — Pipeline Health tab

- [ ] 📊 Add a **stacked bar chart** — "Daily Downloads by Status" (from `v_download_health`, x = day, color = status: SUCCESS / FAILED / SKIPPED).
- [ ] 📊 Add a **table** — "Data Quality by Feed" showing all columns from `v_data_quality`. Color-code completeness percentages: green ≥ 90%, yellow 70–89%, red < 70%.
  > **Beginner note:** Use Streamlit's `st.dataframe` with `column_config` to apply color formatting, or use pandas `Styler` for more control.
- [ ] 📊 Add a **bar chart** — "Shows with Lowest Audio URL Availability" (bottom 10 feeds by `pct_has_audio_url` from `v_data_quality`). This immediately shows which feeds are problematic.
- [ ] 📊 Keep the existing "Recent Downloads" table from the original app.

### 4f — Sidebar filters

- [ ] 📊 Add a sidebar with global filters that affect all charts on all tabs:
  - Date range picker (`st.date_input` with a range) — filters all queries to `pub_date BETWEEN start AND end`
  - Category multiselect — filters by category
  - "Active feeds only" checkbox — filters to feeds with `last_fetched_at` within the last 7 days
- [ ] 📝 Update all `load_data()` query calls to pass the sidebar filter values as SQL parameters (use `%s` placeholders with pandas `read_sql`, never f-strings — this is a basic SQL injection protection habit).

---

## Stage 5 — Add Data Quality Logging
> **Goal:** Make pipeline failures and data gaps visible and persistent.  
> **Why:** Right now, if a feed fails or returns garbage, you'd never know without reading logs. Good data engineers instrument everything.

### Tasks

- [ ] 🗄️ In `init-schema.yaml`, add a new table:
  ```sql
  CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id          TEXT PRIMARY KEY,
    flow_id         TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    status          TEXT,         -- 'success', 'partial', 'failed'
    feeds_processed INTEGER,
    episodes_inserted INTEGER,
    episodes_skipped  INTEGER,
    download_success  INTEGER,
    download_failed   INTEGER,
    error_message     TEXT
  );
  ```
- [ ] 🔄 In `rss-podcast-poc.yaml`, add a `start_log` task at the very beginning that inserts a row into `pipeline_run_log` with `status = 'running'` and the current `execution.id` as `run_id`.
- [ ] 🔄 Add an `update_log` task at the very end of the flow that updates that same row with the final counts and `status = 'success'`.
- [ ] 🔄 Add an `errors` block at the flow level that catches any failure and updates the log row with `status = 'failed'` and the error message. 
  > **Beginner note:** In Kestra, the `errors` block at the top level of a flow runs only when another task fails. It's like a try/catch for your whole flow. [Kestra error handling docs](https://kestra.io/docs/workflow-components/errors).
- [ ] 📊 In the dashboard's Pipeline Health tab, add a **table** showing the last 20 rows of `pipeline_run_log` — run timestamp, status, feeds processed, episodes inserted, download stats.

---

## Stage 6 — Polish and Production-Readiness
> **Goal:** Clean up rough edges, improve reliability, and make the project presentable.  
> **Why:** A learning project that actually works reliably is more valuable than one that's theoretically complete.

### Tasks

- [x] 📝 Add a `README.md` to the project root explaining what the project does, how to run it locally (prerequisites, `.env` setup, `docker compose up`), and what each service is for. Include a screenshot of the dashboard.
- [x] 📝 Add retry logic to the audio download task — wrap the `requests.get` call in a loop with `max_retries = 3` and a 2-second sleep between retries. This alone will dramatically improve download success rates.
- [x] 📝 Add a timeout to all HTTP calls (`requests.get(..., timeout=30)`) — the current code has `timeout=60` for audio files, but the RSS fetch itself has no timeout. A single hanging feed can stall the whole pipeline.
- [x] 🔄 Split the main flow into two separate flows:
  - `ingest-metadata.yaml` — RSS fetch → extract → store metadata only (runs every hour)
  - `download-audio.yaml` — reads undownloaded episodes from DB → downloads audio (runs every 6 hours, heavier task)
  This separation means metadata is always fresh even if audio downloads are slow.
- [x] 📝 In `dashboard/requirements.txt`, pin all dependency versions (they already are — keep them pinned and update them deliberately, not automatically).
- [x] 📝 Add a `.dockerignore` file in `dashboard/` that excludes `.env`, `.git`, `__pycache__`, and `*.pyc` from the Docker build context.
- [ ] 🧪 Do a clean end-to-end test: `docker compose down -v` (removes all volumes and data), then `docker compose up`, run `init-schema`, run `seed-feeds`, run the pipeline, open the dashboard. Everything should work from scratch. *(Manual verification required)*

---

## Appendix A — Kestra Concepts Quick Reference

| Term | What it means |
|---|---|
| **Flow** | A YAML file that defines a pipeline. Like a recipe. |
| **Task** | One step inside a flow (download a file, run a script, query the DB). |
| **Trigger** | What starts a flow automatically (a schedule, a webhook, another flow finishing). |
| **Namespace** | A folder-like grouping for flows. `deeptech` in your project. |
| **pluginDefaults** | Settings shared by all tasks of a given type in the flow (e.g., the DB connection string). |
| **Variables** | Reusable values inside a flow, defined once and referenced with `{{vars.name}}`. |
| **Outputs** | Files or values that a task produces and the next task can consume. |
| **ForEach** | A loop task that runs a set of sub-tasks once per item in a list. |
| **Errors block** | Tasks that run only when another task in the flow fails. |

---

## Appendix B — SQL Patterns for Beginners

**Counting rows in a table:**
```sql
SELECT COUNT(*) FROM podcast_metadata;
```

**Grouping and counting:**
```sql
SELECT source, COUNT(*) AS episode_count
FROM podcast_metadata
GROUP BY source
ORDER BY episode_count DESC;
```

**Finding the average of a column per group:**
```sql
SELECT category, AVG(duration_seconds) / 60.0 AS avg_minutes
FROM podcast_metadata
WHERE duration_seconds IS NOT NULL
GROUP BY category;
```

**Filtering by date range:**
```sql
SELECT * FROM podcast_metadata
WHERE pub_date >= NOW() - INTERVAL '7 days';
```

**Joining two tables:**
```sql
SELECT m.title, m.source, d.status, d.downloaded_at
FROM podcast_metadata m
JOIN podcast_downloads d ON m.guid = d.guid
ORDER BY d.downloaded_at DESC;
```

**Checking for NULLs (data quality):**
```sql
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN audio_url IS NULL THEN 1 ELSE 0 END) AS missing_audio_url,
  SUM(CASE WHEN duration_seconds IS NULL THEN 1 ELSE 0 END) AS missing_duration
FROM podcast_metadata;
```

---

## Appendix C — Recommended Learning Resources

- **Kestra documentation:** https://kestra.io/docs  
- **PostgreSQL tutorial (beginner):** https://www.postgresqltutorial.com  
- **Streamlit documentation:** https://docs.streamlit.io  
- **Plotly Express charts in Python:** https://plotly.com/python/plotly-express/  
- **Python `requests` library:** https://docs.python-requests.org/en/latest/  
- **Understanding RSS/XML feeds:** https://www.rssboard.org/rss-specification  
- **iTunes Podcast RSS tags reference:** https://podcasters.apple.com/support/823-podcast-requirements  

---

*End of plan. Good luck — you're building something real.*
