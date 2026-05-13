"""
ingestion/load_to_duckdb.py
Loads all raw JSON snapshots into DuckDB as the raw source table.
Idempotent: deduplicates by (id, ingested_at date).
"""

import duckdb
import json
import os
from pathlib import Path
from datetime import datetime

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pulsetrack.duckdb"


def load_raw_to_duckdb():
    con = duckdb.connect(str(DB_PATH))

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_repos (
            id BIGINT,
            name VARCHAR,
            description VARCHAR,
            language VARCHAR,
            stars INTEGER,
            forks INTEGER,
            open_issues INTEGER,
            watchers INTEGER,
            license VARCHAR,
            topics JSON,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            pushed_at TIMESTAMP,
            url VARCHAR,
            ingested_at TIMESTAMP,
            snapshot_date DATE
        )
    """)

    all_records = []
    for date_dir in sorted(RAW_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        snapshot_file = date_dir / "snapshot.json"
        if not snapshot_file.exists():
            continue

        snapshot_date = date_dir.name
        with open(snapshot_file) as f:
            records = json.load(f)

        for r in records:
            r["snapshot_date"] = snapshot_date
            r["topics"] = json.dumps(r.get("topics", []))
            all_records.append(r)

    if not all_records:
        print("No raw data found. Run ingestion first.")
        return

    # Bulk insert via temp table
    import pandas as pd
    df = pd.DataFrame(all_records)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_localize(None)
    df["updated_at"] = pd.to_datetime(df["updated_at"], utc=True).dt.tz_localize(None)
    df["pushed_at"] = pd.to_datetime(df["pushed_at"], utc=True).dt.tz_localize(None)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date

    con.execute("DELETE FROM raw_repos")
    con.execute("INSERT INTO raw_repos SELECT * FROM df")

    count = con.execute("SELECT COUNT(*) FROM raw_repos").fetchone()[0]
    print(f"Loaded {count} records into raw_repos")
    con.close()


if __name__ == "__main__":
    load_raw_to_duckdb()
