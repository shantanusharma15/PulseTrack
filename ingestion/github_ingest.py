"""
ingestion/github_ingest.py
Fetches trending repositories from GitHub Search API (no auth needed for light use).
Saves raw JSON snapshots partitioned by date.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.github.com/search/repositories"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

_langs_env = os.getenv("PULSETRACK_LANGUAGES", "python,javascript,go,rust,java")
LANGUAGES = [l.strip() for l in _langs_env.split(",")]

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
_token = os.getenv("GITHUB_TOKEN", "").strip()
if _token:
    HEADERS["Authorization"] = f"token {_token}"
    print("  Using GitHub token (5000 req/hr rate limit)")


def fetch_trending(language: str, days_back: int = 7, per_page: int = 50) -> list[dict]:
    """Fetch repositories created in last N days, sorted by stars."""
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": f"language:{language} created:>{since}",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }
    resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def extract_fields(repo: dict, language: str) -> dict:
    """Flatten the fields we care about."""
    return {
        "id": repo["id"],
        "name": repo["full_name"],
        "description": repo.get("description", ""),
        "language": language,
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "open_issues": repo["open_issues_count"],
        "watchers": repo["watchers_count"],
        "license": repo.get("license", {}).get("spdx_id") if repo.get("license") else None,
        "topics": repo.get("topics", []),
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "pushed_at": repo["pushed_at"],
        "url": repo["html_url"],
        "ingested_at": datetime.utcnow().isoformat(),
    }


def run_ingestion(languages: list[str] = LANGUAGES):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = RAW_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    all_repos = []
    for lang in languages:
        print(f"  Fetching: {lang}")
        try:
            repos = fetch_trending(lang)
            cleaned = [extract_fields(r, lang) for r in repos]
            all_repos.extend(cleaned)

            # Per-language file for debugging
            lang_file = out_dir / f"{lang}.json"
            with open(lang_file, "w") as f:
                json.dump(cleaned, f, indent=2)

        except requests.HTTPError as e:
            print(f"  [WARN] {lang} failed: {e}")

    # Combined daily snapshot
    snapshot_file = out_dir / "snapshot.json"
    with open(snapshot_file, "w") as f:
        json.dump(all_repos, f, indent=2)

    print(f"  Saved {len(all_repos)} repos → {snapshot_file}")
    return len(all_repos)


if __name__ == "__main__":
    print("Running manual ingestion...")
    run_ingestion()
