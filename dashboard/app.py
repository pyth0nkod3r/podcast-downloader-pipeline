import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Podcast Pipeline Monitor",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────
# Custom CSS — premium dark theme
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 2rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    div[data-testid="stMetric"] label {
        color: #8892b0 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e6f1ff !important;
        font-weight: 700 !important;
    }

    h1 {
        background: linear-gradient(90deg, #64ffda, #00d2ff, #7b61ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(100,255,218,0.1) !important;
        border-bottom: 2px solid #64ffda !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────────────────
COLORS = {
    "primary":   "#64ffda",
    "secondary": "#00d2ff",
    "accent":    "#7b61ff",
    "success":   "#00CC96",
    "warning":   "#FFA15A",
    "danger":    "#EF553B",
    "muted":     "#8892b0",
}

CATEGORY_COLORS = px.colors.qualitative.Pastel

PLOTLY_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter", color="#ccd6f6"),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(bgcolor='rgba(0,0,0,0)'),
)


# ─────────────────────────────────────────────────────────
# DB Connection
# ─────────────────────────────────────────────────────────
REQUIRED_TABLES = ['podcast_feeds', 'podcast_metadata', 'podcast_downloads', 'pipeline_run_log']
REQUIRED_VIEWS  = ['v_episodes_clean', 'v_feed_stats', 'v_publishing_heatmap',
                   'v_weekly_volume', 'v_download_health', 'v_data_quality']


@st.cache_resource
def get_db_engine():
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    db_name = os.environ.get('DB_NAME', 'podcast_db')
    db_host = os.environ.get('DB_HOST', 'pgdatabase')
    db_port = os.environ.get('DB_PORT', '5432')
    conn_str = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(conn_str)


@st.cache_data(ttl=300)
def check_schema_health():
    """Return (missing_tables, missing_views, db_reachable)."""
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type IN ('BASE TABLE', 'VIEW')"
            ))
            existing = {row[0] for row in result}
        missing_tables = [t for t in REQUIRED_TABLES if t not in existing]
        missing_views  = [v for v in REQUIRED_VIEWS  if v not in existing]
        return missing_tables, missing_views, True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return REQUIRED_TABLES, REQUIRED_VIEWS, False


@st.cache_data(ttl=60)
def load_data(query, params=None):
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params or {})
        return df
    except Exception as e:
        logger.warning("Query failed: %s — %s", e, query[:120])
        return pd.DataFrame()


def build_cat_filter(selected_categories, category_list, params, col="category"):
    """Build a parameterized IN clause for category filtering.
    Mutates `params` dict in-place, returns SQL fragment string.
    """
    if not selected_categories or len(selected_categories) >= len(category_list):
        return ""
    placeholders = []
    for i, cat in enumerate(selected_categories):
        key = f"cat_{i}"
        placeholders.append(f":{key}")
        params[key] = cat
    return f"AND {col} IN ({', '.join(placeholders)})"


def safe_metric(label, value, fmt=None):
    """Display a metric or dash if data is missing."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        st.metric(label, "—")
    elif fmt:
        st.metric(label, fmt.format(value))
    else:
        st.metric(label, value)


# ─────────────────────────────────────────────────────────
# Schema Health Check
# ─────────────────────────────────────────────────────────
missing_tables, missing_views, db_reachable = check_schema_health()
schema_ok = db_reachable and not missing_tables and not missing_views

if not db_reachable:
    st.error(
        "🚨 **Cannot connect to the database.**\n\n"
        "Make sure the `pgdatabase` service is running:\n"
        "```bash\ndocker compose up pgdatabase -d\n```"
    )
    st.stop()

if not schema_ok:
    all_missing = missing_tables + missing_views
    st.warning(
        "⚠️ **Database schema is not initialized** — the following "
        f"{len(all_missing)} relation(s) are missing:\n\n"
        + ", ".join(f"`{m}`" for m in all_missing)
        + "\n\n**How to fix:** Run the `init-schema` flow in Kestra "
        "(namespace `deeptech`) or execute the SQL from "
        "`flows/init-schema.yaml` directly against the database.\n\n"
        "```bash\n"
        "# Via Kestra UI → deeptech / init-schema → Execute\n"
        "# Or manually:\n"
        "docker compose exec pgdatabase psql -U $DB_USER -d $DB_NAME -f /path/to/schema.sql\n"
        "```"
    )
    st.info("📊 Dashboard will display data once the schema is created and the pipeline has run.")
    st.stop()

# ─────────────────────────────────────────────────────────
# Sidebar — global filters (Stage 4f)
# ─────────────────────────────────────────────────────────
st.sidebar.title("🎙️ Filters")

# Category filter
all_categories = load_data("SELECT DISTINCT category FROM podcast_metadata WHERE category IS NOT NULL ORDER BY category")
category_list = all_categories['category'].tolist() if not all_categories.empty else []
selected_categories = st.sidebar.multiselect("Category", category_list, default=category_list)

# Date range
default_start = datetime.now() - timedelta(days=365 * 3)
date_range = st.sidebar.date_input(
    "Publication date range",
    value=(default_start.date(), datetime.now().date()),
    max_value=datetime.now().date()
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = default_start.date()
    end_date = datetime.now().date()

# Build parameterized filter values (used by each query individually)
# Each query call site builds its own params dict and calls build_cat_filter()
filter_start_date = str(start_date)
filter_end_date = str(end_date)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Podcast Pipeline Monitor v2.0")

# ─────────────────────────────────────────────────────────
# Title
# ─────────────────────────────────────────────────────────
st.title("🎙️ Podcast Pipeline Monitor")
st.markdown("Real-time observability into the automated podcast ingestion workflow.")

# ─────────────────────────────────────────────────────────
# Tabs (Stage 4a)
# ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎙️ Shows", "📅 Trends", "🔧 Pipeline Health"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════
with tab1:
    # KPI metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    p1 = {}; cf1 = build_cat_filter(selected_categories, category_list, p1)
    total_eps = load_data(f"SELECT COUNT(*) as c FROM podcast_metadata WHERE 1=1 {cf1}", p1)
    total_feeds = load_data("SELECT COUNT(*) as c FROM podcast_feeds WHERE is_active = TRUE")
    p2 = {}; cf2 = build_cat_filter(selected_categories, category_list, p2)
    total_hours = load_data(f"SELECT COALESCE(SUM(duration_seconds) / 3600.0, 0) as c FROM podcast_metadata WHERE duration_seconds IS NOT NULL {cf2}", p2)
    p3 = {}; cf3 = build_cat_filter(selected_categories, category_list, p3)
    recent_eps = load_data(f"SELECT COUNT(*) as c FROM podcast_metadata WHERE created_at >= NOW() - INTERVAL '7 days' {cf3}", p3)
    dl_rate = load_data("SELECT ROUND(100.0 * SUM(CASE WHEN status IN ('success','skipped') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as c FROM podcast_downloads")

    with col1:
        val = total_eps['c'].iloc[0] if not total_eps.empty else 0
        safe_metric("Total Episodes", f"{val:,}", None)
    with col2:
        val = total_feeds['c'].iloc[0] if not total_feeds.empty else 0
        safe_metric("Active Feeds", val)
    with col3:
        val = total_hours['c'].iloc[0] if not total_hours.empty else 0
        safe_metric("Total Hours of Audio", f"{val:,.0f}")
    with col4:
        val = recent_eps['c'].iloc[0] if not recent_eps.empty else 0
        safe_metric("Added (Last 7 Days)", val)
    with col5:
        val = dl_rate['c'].iloc[0] if not dl_rate.empty else 0
        safe_metric("Download Success %", f"{val}%")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Top 15 Shows by Episode Count")
        p_top = {}; cf_top = build_cat_filter(selected_categories, category_list, p_top)
        df = load_data(f"""
            SELECT source, COUNT(*) AS total_episodes
            FROM podcast_metadata WHERE 1=1 {cf_top}
            GROUP BY source ORDER BY 2 DESC LIMIT 15
        """, p_top)
        if not df.empty:
            fig = px.bar(df, y='source', x='total_episodes', orientation='h',
                         color='total_episodes',
                         color_continuous_scale=['#16213e', '#64ffda'])
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False,
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available. Run the pipeline first.")

    with row1_col2:
        st.subheader("Episodes by Category")
        p_pie = {}; cf_pie = build_cat_filter(selected_categories, category_list, p_pie)
        df = load_data(f"""
            SELECT category, COUNT(*) AS total
            FROM podcast_metadata WHERE category IS NOT NULL {cf_pie}
            GROUP BY category ORDER BY 2 DESC
        """, p_pie)
        if not df.empty:
            fig = px.pie(df, names='category', values='total', hole=0.45,
                         color_discrete_sequence=CATEGORY_COLORS)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    st.subheader("Average Episode Duration by Category")
    p_dur = {}; cf_dur = build_cat_filter(selected_categories, category_list, p_dur)
    df = load_data(f"""
        SELECT category, ROUND(AVG(duration_seconds) / 60.0, 1) AS avg_minutes
        FROM podcast_metadata
        WHERE duration_seconds IS NOT NULL AND category IS NOT NULL {cf_dur}
        GROUP BY category ORDER BY 2 DESC
    """, p_dur)
    if not df.empty:
        fig = px.bar(df, x='category', y='avg_minutes',
                     color='avg_minutes',
                     color_continuous_scale=['#7b61ff', '#64ffda'],
                     labels={'avg_minutes': 'Avg Duration (min)', 'category': 'Category'})
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No duration data available yet.")


# ═══════════════════════════════════════════════════════════
# TAB 2 — SHOWS
# ═══════════════════════════════════════════════════════════
with tab2:
    feeds_df = load_data("SELECT feed_name FROM podcast_feeds WHERE is_active = TRUE ORDER BY feed_name")
    if not feeds_df.empty:
        selected_feed = st.selectbox("Select a podcast", feeds_df['feed_name'].tolist())

        # Stats row
        stats = load_data(
            "SELECT COUNT(*) AS total_episodes, "
            "ROUND(AVG(duration_seconds) / 60.0, 1) AS avg_duration_min, "
            "MAX(pub_date) AS latest_episode, "
            "SUM(CASE WHEN explicit THEN 1 ELSE 0 END) AS explicit_count "
            "FROM podcast_metadata WHERE source = :feed",
            {"feed": selected_feed}
        )

        if not stats.empty and stats['total_episodes'].iloc[0] > 0:
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                safe_metric("Total Episodes", stats['total_episodes'].iloc[0])
            with sc2:
                safe_metric("Avg Duration (min)", stats['avg_duration_min'].iloc[0])
            with sc3:
                latest = stats['latest_episode'].iloc[0]
                safe_metric("Latest Episode", str(latest)[:10] if latest else "—")
            with sc4:
                safe_metric("Explicit Episodes", stats['explicit_count'].iloc[0])

            st.markdown("---")

            show_col1, show_col2 = st.columns(2)

            with show_col1:
                st.subheader("Episode Duration Over Time")
                dur_df = load_data(
                    "SELECT pub_date, ROUND(duration_seconds / 60.0, 1) AS duration_minutes "
                    "FROM podcast_metadata "
                    "WHERE source = :feed AND pub_date IS NOT NULL AND duration_seconds IS NOT NULL "
                    "ORDER BY pub_date",
                    {"feed": selected_feed}
                )
                if not dur_df.empty:
                    fig = px.line(dur_df, x='pub_date', y='duration_minutes',
                                 markers=True, line_shape='spline',
                                 labels={'pub_date': 'Date', 'duration_minutes': 'Duration (min)'})
                    fig.update_traces(line_color=COLORS['primary'], line_width=2)
                    fig.update_layout(**PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No duration data for this feed.")

            with show_col2:
                st.subheader("Episodes Published Per Month")
                monthly_df = load_data(
                    "SELECT DATE_TRUNC('month', pub_date) AS month, COUNT(*) AS count "
                    "FROM podcast_metadata "
                    "WHERE source = :feed AND pub_date IS NOT NULL "
                    "GROUP BY 1 ORDER BY 1",
                    {"feed": selected_feed}
                )
                if not monthly_df.empty:
                    fig = px.bar(monthly_df, x='month', y='count',
                                 color_discrete_sequence=[COLORS['secondary']],
                                 labels={'month': 'Month', 'count': 'Episodes'})
                    fig.update_layout(**PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No date data for this feed.")

            st.subheader("Recent Episodes")
            recent_df = load_data(
                "SELECT title, pub_date, ROUND(duration_seconds / 60.0, 1) AS duration_min, "
                "description_word_count "
                "FROM podcast_metadata WHERE source = :feed "
                "ORDER BY pub_date DESC NULLS LAST LIMIT 20",
                {"feed": selected_feed}
            )
            if not recent_df.empty:
                st.dataframe(recent_df, use_container_width=True, hide_index=True,
                             column_config={
                                 "title": "Title",
                                 "pub_date": st.column_config.DatetimeColumn("Published", format="YYYY-MM-DD"),
                                 "duration_min": "Duration (min)",
                                 "description_word_count": "Desc. Words",
                             })
        else:
            st.info(f"No episodes found for **{selected_feed}**. Run the pipeline to fetch data.")
    else:
        st.warning("No feeds found in the catalog. Run `seed-feeds` first.")


# ═══════════════════════════════════════════════════════════
# TAB 3 — TRENDS
# ═══════════════════════════════════════════════════════════
with tab3:
    st.subheader("Weekly Episode Volume by Category")
    weekly_df = load_data(f"""
        SELECT pub_week, category, episodes_published
        FROM v_weekly_volume
        WHERE pub_week IS NOT NULL
        ORDER BY pub_week
    """)
    if not weekly_df.empty:
        fig = px.line(weekly_df, x='pub_week', y='episodes_published', color='category',
                      labels={'pub_week': 'Week', 'episodes_published': 'Episodes'},
                      color_discrete_sequence=CATEGORY_COLORS)
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No weekly data available yet.")

    st.markdown("---")

    trend_col1, trend_col2 = st.columns(2)

    with trend_col1:
        st.subheader("When Do Creators Publish?")
        heatmap_df = load_data("SELECT * FROM v_publishing_heatmap")
        if not heatmap_df.empty:
            pivot = heatmap_df.pivot_table(index='day_of_week', columns='hour_of_day',
                                           values='episode_count', fill_value=0)
            day_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            pivot.index = [day_labels[int(i)] for i in pivot.index]
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=[f"{int(h)}:00" for h in pivot.columns],
                y=pivot.index,
                colorscale=[[0, '#0a192f'], [0.5, '#16213e'], [1, '#64ffda']],
                hoverongaps=False,
            ))
            fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Hour of Day", yaxis_title="Day of Week")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No publishing data available yet.")

    with trend_col2:
        st.subheader("Duration vs. Description Length")
        p_sc = {}; cf_sc = build_cat_filter(selected_categories, category_list, p_sc)
        scatter_df = load_data(f"""
            SELECT duration_minutes, description_word_count, category, title
            FROM v_episodes_clean
            WHERE duration_minutes IS NOT NULL AND description_word_count IS NOT NULL
                  AND description_word_count > 0 {cf_sc}
            LIMIT 2000
        """, p_sc)
        if not scatter_df.empty:
            fig = px.scatter(scatter_df, x='description_word_count', y='duration_minutes',
                             color='category', hover_data=['title'],
                             labels={'description_word_count': 'Description Words',
                                     'duration_minutes': 'Duration (min)'},
                             color_discrete_sequence=CATEGORY_COLORS,
                             opacity=0.6)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available yet.")

    st.subheader("Average Episode Duration Trend")
    p_dt = {}; cf_dt = build_cat_filter(selected_categories, category_list, p_dt)
    dur_trend = load_data(f"""
        SELECT pub_week, ROUND(AVG(duration_minutes), 1) AS avg_duration
        FROM v_episodes_clean
        WHERE duration_minutes IS NOT NULL AND pub_week IS NOT NULL {cf_dt}
        GROUP BY pub_week ORDER BY pub_week
    """, p_dt)
    if not dur_trend.empty:
        fig = px.line(dur_trend, x='pub_week', y='avg_duration', markers=True,
                      labels={'pub_week': 'Week', 'avg_duration': 'Avg Duration (min)'},
                      line_shape='spline')
        fig.update_traces(line_color=COLORS['accent'], line_width=3)
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No duration trend data available yet.")


# ═══════════════════════════════════════════════════════════
# TAB 4 — PIPELINE HEALTH
# ═══════════════════════════════════════════════════════════
with tab4:
    health_col1, health_col2 = st.columns([2, 1])

    with health_col1:
        st.subheader("Daily Downloads by Status")
        dl_df = load_data("SELECT * FROM v_download_health WHERE day IS NOT NULL ORDER BY day DESC LIMIT 90")
        if not dl_df.empty:
            fig = px.bar(dl_df, x='day', y='count', color='status',
                         color_discrete_map={'success': COLORS['success'],
                                             'failed': COLORS['danger'],
                                             'skipped': COLORS['warning']},
                         labels={'day': 'Date', 'count': 'Downloads'},
                         barmode='stack')
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No download data available yet.")

    with health_col2:
        st.subheader("Lowest Audio Availability")
        low_audio = load_data("SELECT source, pct_has_audio_url FROM v_data_quality ORDER BY pct_has_audio_url ASC LIMIT 10")
        if not low_audio.empty:
            fig = px.bar(low_audio, y='source', x='pct_has_audio_url', orientation='h',
                         color='pct_has_audio_url',
                         color_continuous_scale=['#EF553B', '#FFA15A', '#00CC96'],
                         labels={'pct_has_audio_url': 'Audio URL %', 'source': ''})
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False,
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data quality data available yet.")

    st.markdown("---")

    st.subheader("Data Quality by Feed")
    dq_df = load_data("SELECT * FROM v_data_quality")
    if not dq_df.empty:
        def color_pct(val):
            if isinstance(val, (int, float)):
                if val >= 90:
                    return 'background-color: rgba(0,204,150,0.2)'
                elif val >= 70:
                    return 'background-color: rgba(255,161,90,0.2)'
                else:
                    return 'background-color: rgba(239,85,59,0.2)'
            return ''

        pct_cols = ['pct_has_title', 'pct_has_audio_url', 'pct_has_duration', 'pct_has_pub_date', 'pct_has_category']
        styled = dq_df.style.map(color_pct, subset=[c for c in pct_cols if c in dq_df.columns])
        st.dataframe(styled, use_container_width=True, hide_index=True,
                     column_config={
                         "source": "Feed",
                         "total": "Total Episodes",
                         "pct_has_title": st.column_config.NumberColumn("% Title", format="%.1f%%"),
                         "pct_has_audio_url": st.column_config.NumberColumn("% Audio URL", format="%.1f%%"),
                         "pct_has_duration": st.column_config.NumberColumn("% Duration", format="%.1f%%"),
                         "pct_has_pub_date": st.column_config.NumberColumn("% Pub Date", format="%.1f%%"),
                         "pct_has_category": st.column_config.NumberColumn("% Category", format="%.1f%%"),
                     })
    else:
        st.info("No data quality data available yet.")

    st.markdown("---")

    st.subheader("Pipeline Run Log")
    run_log = load_data("SELECT * FROM pipeline_run_log ORDER BY started_at DESC LIMIT 20")
    if not run_log.empty:
        st.dataframe(run_log, use_container_width=True, hide_index=True,
                     column_config={
                         "run_id": "Run ID",
                         "flow_id": "Flow",
                         "started_at": st.column_config.DatetimeColumn("Started", format="YYYY-MM-DD HH:mm"),
                         "finished_at": st.column_config.DatetimeColumn("Finished", format="YYYY-MM-DD HH:mm"),
                         "status": "Status",
                         "feeds_processed": "Feeds",
                         "episodes_inserted": "Inserted",
                         "download_success": "DL OK",
                         "download_failed": "DL Fail",
                         "error_message": "Error",
                     })
    else:
        st.info("No pipeline runs logged yet. Run the main pipeline to see logs.")

    st.markdown("---")

    st.subheader("Recent Downloads")
    recent_dl = load_data("""
        SELECT guid, file_path, status, downloaded_at
        FROM podcast_downloads
        ORDER BY downloaded_at DESC
        LIMIT 50
    """)
    if not recent_dl.empty:
        st.dataframe(recent_dl, use_container_width=True, hide_index=True,
                     column_config={
                         "guid": "Episode ID",
                         "file_path": "File Path",
                         "status": "Status",
                         "downloaded_at": st.column_config.DatetimeColumn("Downloaded At", format="YYYY-MM-DD HH:mm:ss"),
                     })
    else:
        st.info("No downloads recorded yet.")
