#!/usr/bin/env bash
# run.sh — Full PulseTrack pipeline + dashboard launcher
# Usage:  bash run.sh              (full run)
#         bash run.sh --skip-ingest (transform + dashboard only)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/../.venv/Scripts/python.exe"

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SKIP_INGEST=false
for arg in "$@"; do
  [[ "$arg" == "--skip-ingest" ]] && SKIP_INGEST=true
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   📡  PulseTrack — GitHub Intelligence Pipeline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
  echo "  ✓ Loaded .env configuration"
fi

DB_PATH="${PULSETRACK_DB_PATH:-data/pulsetrack.duckdb}"

echo "▶ [1/5] Installing dependencies..."
"$PYTHON" -m pip install -q -r requirements.txt
echo "  ✓ Dependencies ready"

if [ "$SKIP_INGEST" = false ]; then
  echo ""
  echo "▶ [2/5] Ingesting from GitHub API..."
  "$PYTHON" ingestion/github_ingest.py
else
  echo ""
  echo "▶ [2/5] Skipping ingestion (--skip-ingest flag)"
fi

echo ""
echo "▶ [3/5] Loading raw JSON → DuckDB..."
$PYTHON ingestion/load_to_duckdb.py

echo ""
echo "▶ [4/5] Running dbt transformations..."
cd dbt_project
PULSETRACK_DB_PATH="../${DB_PATH}" \
  "$PYTHON" -m dbt.cli.main run --profiles-dir profiles --project-dir . --quiet
echo "  ✓ dbt models built"
echo ""
echo "  Running dbt tests..."
PULSETRACK_DB_PATH="../${DB_PATH}" \
  "$PYTHON" -m dbt.cli.main test --profiles-dir profiles --project-dir . --quiet && \
  echo "  ✓ All data quality tests passed" || \
  echo "  ⚠️  Some tests failed — check dbt_project/target/run_results.json"
cd ..

echo ""
echo "▶ [5/5] Running breakout detector..."
"$PYTHON" ingestion/breakout_detector.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Pipeline complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═══════════════════════════════════════════════════════════════════════"
echo ""
echo "  Dashboard → http://localhost:8501"
echo "  Airflow   → docker compose up -d  (http://localhost:8080)"
echo ""
echo "  Tip: Run again to accumulate snapshots for trend charts."
echo "  Tip: Add your GitHub token to .env for 5000 req/hr."
echo ""

streamlit run dashboard/app.py
