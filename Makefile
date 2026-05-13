# PulseTrack Makefile
# Usage: make <target>

.PHONY: help install ingest load transform pipeline dashboard docker-up docker-down clean test

PYTHON      = python3
DBT_DIR     = dbt_project
PROFILES    = dbt_project/profiles
DB_PATH     = data/pulsetrack.duckdb

help:
	@echo ""
	@echo "  📡 PulseTrack — Available Commands"
	@echo "  ──────────────────────────────────"
	@echo "  make install     Install all Python dependencies"
	@echo "  make ingest      Fetch latest data from GitHub API"
	@echo "  make load        Load raw JSON snapshots into DuckDB"
	@echo "  make transform   Run dbt models (staging → marts)"
	@echo "  make test        Run dbt data quality tests"
	@echo "  make pipeline    Run full pipeline: ingest + load + transform"
	@echo "  make dashboard   Launch Streamlit dashboard"
	@echo "  make docker-up   Start Airflow via Docker Compose"
	@echo "  make docker-down Stop Airflow containers"
	@echo "  make clean       Remove generated data and dbt artifacts"
	@echo ""

install:
	pip install -r requirements.txt

ingest:
	@echo "▶ Ingesting from GitHub API..."
	$(PYTHON) ingestion/github_ingest.py

load:
	@echo "▶ Loading raw data into DuckDB..."
	$(PYTHON) ingestion/load_to_duckdb.py

transform:
	@echo "▶ Running dbt transformations..."
	cd $(DBT_DIR) && PULSETRACK_DB_PATH=../$(DB_PATH) \
		dbt run --profiles-dir profiles --project-dir .

test:
	@echo "▶ Running dbt data quality tests..."
	cd $(DBT_DIR) && PULSETRACK_DB_PATH=../$(DB_PATH) \
		dbt test --profiles-dir profiles --project-dir .

pipeline: ingest load transform
	@echo "✅ Full pipeline complete."

dashboard:
	@echo "▶ Launching dashboard at http://localhost:8501"
	streamlit run dashboard/app.py

docker-up:
	@echo "▶ Starting Airflow (this takes ~60 seconds)..."
	docker compose up -d
	@echo "   Airflow UI: http://localhost:8080 (admin/admin)"

docker-down:
	docker compose down

clean:
	rm -rf data/raw data/*.duckdb
	cd $(DBT_DIR) && dbt clean --profiles-dir profiles --project-dir . 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned."
