import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os

# Configure the Streamlit page
st.set_page_config(
    page_title="Podcast Pipeline Monitor",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    h1, h2, h3 {
        color: #FAFAFA;
        font-family: 'Inter', sans-serif;
    }
    .stMetric {
        background-color: #1E2127;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_engine():
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    db_name = os.environ.get('DB_NAME', 'podcast_db')
    db_host = os.environ.get('DB_HOST', 'pgdatabase')
    db_port = os.environ.get('DB_PORT', '5432')
    
    conn_str = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(conn_str)

@st.cache_data(ttl=60)
def load_data(query):
    engine = get_db_engine()
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

st.title("🎙️ Podcast Pipeline Monitor")
st.markdown("Real-time observability into the automated podcast ingestion workflow.")

# Create top-level metrics
col1, col2, col3, col4 = st.columns(4)

try:
    total_episodes_df = load_data("SELECT COUNT(*) as count FROM podcast_metadata")
    total_episodes = total_episodes_df['count'].iloc[0] if not total_episodes_df.empty else 0
    
    total_downloads_df = load_data("SELECT COUNT(*) as count FROM podcast_downloads WHERE status = 'SUCCESS'")
    total_downloads = total_downloads_df['count'].iloc[0] if not total_downloads_df.empty else 0
    
    failed_downloads_df = load_data("SELECT COUNT(*) as count FROM podcast_downloads WHERE status = 'FAILED'")
    failed_downloads = failed_downloads_df['count'].iloc[0] if not failed_downloads_df.empty else 0

    success_rate = (total_downloads / (total_downloads + failed_downloads) * 100) if (total_downloads + failed_downloads) > 0 else 0

    col1.metric("Total Episodes Extracted", f"{total_episodes:,}")
    col2.metric("Successful Downloads", f"{total_downloads:,}")
    col3.metric("Failed Downloads", f"{failed_downloads:,}")
    col4.metric("Download Success Rate", f"{success_rate:.1f}%")

except Exception as e:
    st.warning("Database might not be initialized yet. Run the pipeline to populate data.")

st.markdown("---")

# Layout for charts
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Episodes by Source")
    episodes_by_source = load_data("""
        SELECT source, COUNT(*) AS episode_count 
        FROM podcast_metadata 
        GROUP BY source 
        ORDER BY 2 DESC
    """)
    if not episodes_by_source.empty:
        fig1 = px.bar(
            episodes_by_source, 
            x='source', 
            y='episode_count',
            color='source',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'source': 'Podcast Source', 'episode_count': 'Episodes'}
        )
        fig1.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available.")

with row1_col2:
    st.subheader("Episodes Added Over Time")
    episodes_over_time = load_data("""
        SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*) AS episode_count 
        FROM podcast_metadata 
        GROUP BY 1 
        ORDER BY 1
    """)
    if not episodes_over_time.empty:
        fig2 = px.line(
            episodes_over_time, 
            x='day', 
            y='episode_count',
            markers=True,
            line_shape='spline',
            labels={'day': 'Date', 'episode_count': 'Episodes Added'}
        )
        fig2.update_traces(line_color='#00D2FF', line_width=3)
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available.")

row2_col1, row2_col2 = st.columns([1, 2])

with row2_col1:
    st.subheader("Download Status")
    status_breakdown = load_data("""
        SELECT status, COUNT(*) AS count 
        FROM podcast_downloads 
        GROUP BY status 
        ORDER BY 2 DESC
    """)
    if not status_breakdown.empty:
        fig3 = px.pie(
            status_breakdown, 
            names='status', 
            values='count',
            hole=0.4,
            color='status',
            color_discrete_map={'SUCCESS': '#00CC96', 'FAILED': '#EF553B', 'PENDING': '#FFA15A'}
        )
        fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No data available.")

with row2_col2:
    st.subheader("Recent Downloads")
    recent_downloads = load_data("""
        SELECT guid, file_path, status, downloaded_at 
        FROM podcast_downloads 
        ORDER BY downloaded_at DESC 
        LIMIT 50
    """)
    if not recent_downloads.empty:
        st.dataframe(
            recent_downloads, 
            use_container_width=True,
            column_config={
                "guid": "Episode ID",
                "file_path": "File Path",
                "status": "Status",
                "downloaded_at": st.column_config.DatetimeColumn("Downloaded At", format="YYYY-MM-DD HH:mm:ss")
            },
            hide_index=True
        )
    else:
        st.info("No data available.")

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
