"""
ingestion/breakout_detector.py
Detects "breakout" repositories — repos that gained disproportionate stars
relative to their age and language baseline. Writes results to DuckDB.

Run after pipeline:  python ingestion/breakout_detector.py
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pulsetrack.duckdb"

BREAKOUT_SQL = """
-- Breakout repos: stars-per-day > 3x their language's median stars-per-day
-- and absolute stars > 50 (filters out brand-new 1-star repos)

WITH repo_velocity AS (
    SELECT
        repo_id,
        repo_name,
        language,
        stars,
        forks,
        repo_age_days,
        snapshot_date,
        url,
        -- Stars per day of existence (velocity)
        CASE
            WHEN repo_age_days > 0 THEN ROUND(stars::FLOAT / repo_age_days, 2)
            ELSE stars::FLOAT
        END AS stars_per_day
    FROM mart_top_repos
),

lang_median AS (
    SELECT
        language,
        snapshot_date,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY stars_per_day) AS median_velocity
    FROM repo_velocity
    GROUP BY 1, 2
),

breakouts AS (
    SELECT
        rv.snapshot_date,
        rv.language,
        rv.repo_name,
        rv.stars,
        rv.forks,
        rv.repo_age_days,
        rv.stars_per_day,
        lm.median_velocity,
        ROUND(rv.stars_per_day / NULLIF(lm.median_velocity, 0), 1) AS velocity_multiplier,
        rv.url
    FROM repo_velocity rv
    JOIN lang_median lm
        ON rv.language = lm.language
        AND rv.snapshot_date = lm.snapshot_date
    WHERE rv.stars >= 50
      AND rv.stars_per_day > (lm.median_velocity * 3)
)

SELECT * FROM breakouts
ORDER BY velocity_multiplier DESC, stars DESC
"""


def detect_and_store():
    if not DB_PATH.exists():
        print("No database found. Run the full pipeline first.")
        return

    con = duckdb.connect(str(DB_PATH))

    try:
        con.execute("SELECT 1 FROM mart_top_repos LIMIT 1")
    except Exception:
        print("mart_top_repos not found. Run dbt transformations first.")
        con.close()
        return

    # Create/replace breakout table
    con.execute("CREATE OR REPLACE TABLE breakout_repos AS " + BREAKOUT_SQL)

    count = con.execute("SELECT COUNT(*) FROM breakout_repos").fetchone()[0]
    print(f"\n{'━'*50}")
    print(f"  🚀 Breakout Detector Results: {count} repos found")
    print(f"{'━'*50}")

    if count == 0:
        print("  No breakouts detected in current snapshot.")
        print("  (Need more data — run pipeline a few more times)")
    else:
        rows = con.execute("""
            SELECT repo_name, language, stars, stars_per_day,
                   velocity_multiplier, url
            FROM breakout_repos
            ORDER BY velocity_multiplier DESC
            LIMIT 10
        """).fetchall()

        print(f"  {'Repo':<35} {'Lang':<12} {'Stars':>7} {'⭐/day':>8} {'Mult':>6}")
        print(f"  {'-'*35} {'-'*12} {'-'*7} {'-'*8} {'-'*6}")
        for row in rows:
            name = row[0].split("/")[-1][:34]
            print(f"  {name:<35} {row[1]:<12} {row[2]:>7,} {row[3]:>8.1f} {row[4]:>5.1f}x")

    con.close()
    print(f"\n  Saved to: breakout_repos table in DuckDB")
    print(f"  View in dashboard → Raw Explorer tab:")
    print(f"  SELECT * FROM breakout_repos ORDER BY velocity_multiplier DESC\n")


if __name__ == "__main__":
    detect_and_store()
