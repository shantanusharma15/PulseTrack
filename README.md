# 📡 PulseTrack — GitHub Ecosystem Intelligence Platform

> End-to-end data pipeline: GitHub API → Airflow → dbt → DuckDB → Streamlit dashboard

![Stack](https://img.shields.io/badge/stack-Python%20%7C%20Airflow%20%7C%20dbt%20%7C%20DuckDB%20%7C%20Streamlit-blue)

---

## Architecture

```
GitHub REST API
     │
     ▼
Python Ingestion (requests)
     │  Raw JSON snapshots
     ▼
Apache Airflow DAG (6-hr schedule)
     │
     ▼
DuckDB (raw_repos table)
     │
     ▼
dbt-core (staging → intermediate → marts)
     │  mart_top_repos / mart_language_trends
     ▼
Streamlit Dashboard (Plotly charts + SQL explorer)
```

---

## Quick Start (No Docker)

```bash
git clone <your-repo-url>
cd pulsetrack
bash run.sh
```

This will:
1. Install all Python dependencies
2. Fetch GitHub trending repos (Python, JS, Go, Rust, Java)
3. Load raw JSON → DuckDB
4. Run dbt transformations
5. Launch Streamlit at http://localhost:8501

---

## With Docker + Airflow (Scheduled Pipeline)

```bash
# Start Airflow
docker compose up -d

# Wait ~60 seconds, then open:
# Airflow UI: http://localhost:8080 (admin/admin)
# Trigger DAG: pulsetrack_pipeline

# Run dashboard locally (separate terminal)
pip install streamlit plotly duckdb pandas
streamlit run dashboard/app.py
```

---

## Project Structure

```
pulsetrack/
├── ingestion/
│   ├── github_ingest.py      # GitHub API fetcher
│   └── load_to_duckdb.py     # JSON → DuckDB loader
├── dbt_project/
│   ├── models/
│   │   ├── staging/          # stg_repos (clean + type)
│   │   ├── intermediate/     # int_language_daily (aggregates)
│   │   └── marts/            # mart_top_repos, mart_language_trends
│   └── profiles/             # DuckDB connection config
├── airflow/
│   └── dags/
│       └── pulsetrack_pipeline.py
├── dashboard/
│   └── app.py                # Streamlit dashboard
├── data/                     # Auto-created: raw JSON + DuckDB file
├── docker-compose.yml
├── requirements.txt
└── run.sh                    # One-command runner
```

---

## Dashboard Features

- **KPI cards** — Total stars, repos tracked, hottest language, avg engagement
- **Language trends chart** — Stars over time per language (multi-snapshot)
- **Stars vs Engagement scatter** — Language positioning
- **Top repos bar chart** — Color-coded by engagement score
- **SQL Explorer tab** — Run live queries against DuckDB mart tables

---

## Extending the Project

| Extension | Effort | Impact |
|---|---|---|
| Add GitHub token for 60→5000 req/hr rate limit | 5 min | High |
| Add topic extraction from repo tags | 2 hrs | Medium |
| Push DuckDB → MotherDuck (cloud DuckDB) | 1 hr | High (cloud story) |
| Swap DuckDB for BigQuery + use free tier | 3 hrs | Very High (GCP story) |
| Add dbt tests (not_null, unique, accepted_values) | 1 hr | Medium |
| Add Slack/email alerts on Airflow failure | 1 hr | High |
| Detect "breakout" repos (stars spike > 200% in 24h) | 3 hrs | Very High |
| Deploy Streamlit to Streamlit Cloud (free) | 30 min | High (public URL) |

---


