"""
dashboard/app.py
PulseTrack — GitHub Ecosystem Intelligence Dashboard
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pulsetrack.duckdb"

st.set_page_config(
    page_title="PulseTrack",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }
  .metric-card {
    background: linear-gradient(135deg, #1a1d27 0%, #12141c 100%);
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.5rem;
  }
  .metric-card h3 { color: #64ffda; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; margin: 0; }
  .metric-card .value { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #fff; }
  .metric-card .delta { font-size: 0.8rem; color: #4caf50; }
  .section-header { border-left: 3px solid #64ffda; padding-left: 0.75rem; margin: 1.5rem 0 0.75rem 0; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; }
  .repo-row { background: #1a1d27; border-radius: 8px; padding: 0.6rem 1rem; margin: 0.3rem 0; border: 1px solid #2a2d3e; display: flex; justify-content: space-between; align-items: center; }
  .stTabs [data-baseweb="tab"] { font-family: 'Syne', sans-serif; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = dict(
    paper_bgcolor="#0d0f14",
    plot_bgcolor="#0d0f14",
    font_color="#e2e8f0",
    font_family="Syne",
    colorway=["#64ffda", "#7c83fd", "#ff6b9d", "#ffd166", "#06d6a0", "#ef476f"],
)


# ── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    if not DB_PATH.exists():
        return None, None, None

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        trends = con.execute("SELECT * FROM mart_language_trends ORDER BY snapshot_date, language").df()
        top_repos = con.execute("SELECT * FROM mart_top_repos ORDER BY snapshot_date DESC, language, rank_in_language").df()
        raw_summary = con.execute("""
            SELECT snapshot_date, count(*) as repo_count
            FROM raw_repos GROUP BY 1 ORDER BY 1
        """).df()
    except Exception as e:
        st.error(f"Database error: {e}. Run the pipeline first.")
        return None, None, None
    finally:
        con.close()

    return trends, top_repos, raw_summary


# ── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown("## 📡")
with col_title:
    st.markdown("# PulseTrack")
    st.caption("Real-time GitHub Ecosystem Intelligence · Powered by Python + Airflow + dbt + DuckDB")

st.markdown("---")

trends, top_repos, raw_summary = load_data()

if trends is None or trends.empty:
    st.warning("⚠️ No data yet. Run the pipeline first:")
    st.code("""
# Quick start (no Docker needed):
pip install -r requirements.txt
python ingestion/github_ingest.py
python ingestion/load_to_duckdb.py
cd dbt_project && dbt run --profiles-dir profiles
cd .. && streamlit run dashboard/app.py
    """)
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Filters")
    languages = sorted(trends["language"].unique().tolist())
    selected_langs = st.multiselect("Languages", languages, default=languages)

    snapshots = sorted(trends["snapshot_date"].unique().tolist(), reverse=True)
    latest_snapshot = snapshots[0] if snapshots else None
    selected_snapshot = st.selectbox("Snapshot Date", snapshots)

    st.markdown("---")
    st.markdown("### 📊 Pipeline Stats")
    if raw_summary is not None:
        total_ingested = raw_summary["repo_count"].sum()
        st.metric("Total repos ingested", f"{total_ingested:,}")
        st.metric("Snapshots available", len(snapshots))
        st.metric("Languages tracked", len(languages))

filtered_trends = trends[
    (trends["language"].isin(selected_langs)) &
    (trends["snapshot_date"] == selected_snapshot)
]

# ── KPI Row ────────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    total_stars = int(filtered_trends["total_stars"].sum())
    st.markdown(f"""
    <div class="metric-card">
      <h3>Total Stars (Latest)</h3>
      <div class="value">{total_stars:,}</div>
    </div>""", unsafe_allow_html=True)

with kpi2:
    total_repos = int(filtered_trends["repo_count"].sum())
    st.markdown(f"""
    <div class="metric-card">
      <h3>Repos Tracked</h3>
      <div class="value">{total_repos:,}</div>
    </div>""", unsafe_allow_html=True)

with kpi3:
    top_lang = filtered_trends.loc[filtered_trends["total_stars"].idxmax(), "language"] if not filtered_trends.empty else "—"
    st.markdown(f"""
    <div class="metric-card">
      <h3>Hottest Language</h3>
      <div class="value">{top_lang.title()}</div>
    </div>""", unsafe_allow_html=True)

with kpi4:
    avg_eng = round(filtered_trends["avg_engagement"].mean(), 1) if not filtered_trends.empty else 0
    st.markdown(f"""
    <div class="metric-card">
      <h3>Avg Engagement Score</h3>
      <div class="value">{avg_eng:,.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Language Trends", "🏆 Top Repositories", "🚀 Breakouts", "🔍 Raw Explorer"])

with tab1:
    st.markdown('<div class="section-header">Stars by Language</div>', unsafe_allow_html=True)

    lang_filtered = trends[trends["language"].isin(selected_langs)]

    if len(snapshots) > 1:
        fig_line = px.line(
            lang_filtered,
            x="snapshot_date", y="total_stars",
            color="language",
            title="Cumulative Stars Over Time",
            labels={"total_stars": "Total Stars", "snapshot_date": "Date"},
            markers=True,
        )
        fig_line.update_layout(**PLOTLY_THEME, title_font_size=14)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Trend charts appear after 2+ pipeline runs. Showing snapshot view below.")

    col_bar, col_scatter = st.columns(2)

    with col_bar:
        fig_bar = px.bar(
            filtered_trends.sort_values("total_stars", ascending=True),
            x="total_stars", y="language",
            orientation="h",
            title="Stars per Language (Latest Snapshot)",
            color="language",
        )
        fig_bar.update_layout(**PLOTLY_THEME, showlegend=False, title_font_size=13)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_scatter:
        fig_scatter = px.scatter(
            filtered_trends,
            x="avg_stars", y="avg_engagement",
            size="repo_count",
            color="language",
            title="Avg Stars vs Engagement Score",
            hover_data=["language", "repo_count"],
        )
        fig_scatter.update_layout(**PLOTLY_THEME, title_font_size=13)
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.markdown('<div class="section-header">Top Repositories by Language</div>', unsafe_allow_html=True)

    lang_choice = st.selectbox("Select Language", selected_langs, key="top_repos_lang")

    top = top_repos[
        (top_repos["language"] == lang_choice) &
        (top_repos["snapshot_date"] == selected_snapshot)
    ].head(15)

    if top.empty:
        st.warning("No data for this selection.")
    else:
        fig_top = px.bar(
            top,
            x="stars", y="repo_name",
            orientation="h",
            color="engagement_score",
            color_continuous_scale="Teal",
            title=f"Top {lang_choice.title()} Repos by Stars",
            hover_data=["forks", "open_issues", "repo_age_days"],
        )
        fig_top.update_layout(**PLOTLY_THEME, title_font_size=13, height=450)
        fig_top.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig_top, use_container_width=True)

        st.markdown('<div class="section-header">Repository Details</div>', unsafe_allow_html=True)
        display_df = top[["rank_in_language", "repo_name", "stars", "forks", "open_issues", "license", "url"]].copy()
        display_df.columns = ["#", "Repository", "⭐ Stars", "🍴 Forks", "🐛 Issues", "License", "URL"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)




with tab3:
    st.markdown('<div class="section-header">🚀 Breakout Repositories</div>', unsafe_allow_html=True)
    st.caption("Repos whose star velocity is 3x+ their language median — early signals of viral projects")

    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        breakouts = con.execute("""
            SELECT language, repo_name, stars, stars_per_day,
                   velocity_multiplier, forks, repo_age_days, url
            FROM breakout_repos
            ORDER BY velocity_multiplier DESC
        """).df()
        con.close()

        if breakouts.empty:
            st.info("No breakouts detected yet. Run the pipeline a few more times to accumulate data.")
            st.code("python ingestion/breakout_detector.py")
        else:
            b1, b2 = st.columns(2)
            with b1:
                fig_bv = px.bar(
                    breakouts.head(15).sort_values("velocity_multiplier"),
                    x="velocity_multiplier", y="repo_name",
                    orientation="h", color="language",
                    title="Velocity Multiplier (vs language median)",
                    labels={"velocity_multiplier": "× Median"},
                )
                fig_bv.update_layout(**PLOTLY_THEME, title_font_size=13, height=400)
                st.plotly_chart(fig_bv, use_container_width=True)

            with b2:
                fig_bs = px.scatter(
                    breakouts,
                    x="repo_age_days", y="stars_per_day",
                    size="stars", color="language",
                    hover_data=["repo_name", "velocity_multiplier"],
                    title="Age vs Star Velocity",
                )
                fig_bs.update_layout(**PLOTLY_THEME, title_font_size=13, height=400)
                st.plotly_chart(fig_bs, use_container_width=True)

            st.markdown('<div class="section-header">Breakout Details</div>', unsafe_allow_html=True)
            disp = breakouts[["repo_name","language","stars","stars_per_day","velocity_multiplier","forks","url"]].copy()
            disp.columns = ["Repository","Language","⭐ Stars","⭐/day","Mult (×median)","🍴 Forks","URL"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

    except Exception as e:
        st.info(f"Run breakout detector first: `python ingestion/breakout_detector.py`")
        st.caption(str(e))


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("PulseTrack · Built with Python, Apache Airflow, dbt, DuckDB, Streamlit · Data: GitHub Search API")

with tab4:
    st.markdown('<div class="section-header">Raw SQL Explorer</div>', unsafe_allow_html=True)
    st.caption("Query directly against DuckDB mart tables")

    default_query2 = f"""
SELECT language, repo_name, stars, forks, engagement_score, repo_age_days
FROM mart_top_repos
WHERE snapshot_date = '{selected_snapshot}'
  AND language IN ({', '.join(f"'{l}'" for l in selected_langs)})
ORDER BY stars DESC
LIMIT 50
""".strip()

    user_query2 = st.text_area("SQL Query", value=default_query2, height=120, key="raw_sql")

    if st.button("▶ Run Query", type="primary", key="raw_run"):
        try:
            con = duckdb.connect(str(DB_PATH), read_only=True)
            result = con.execute(user_query2).df()
            con.close()
            st.success(f"{len(result)} rows returned")
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(f"Query failed: {e}")
