"""Refresh worker: CROUS warm, JSON re-verify, and off-path scrapes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db.session import get_session_factory, init_db
from backend.refresh.parsers import PARSERS
from backend.refresh.pipeline import run_pipeline
from backend.repo import VenueRepository

_SOURCES = list(PARSERS.keys()) + ["crous", "distributions", "scrape"]


def run_refresh(source: str = "all") -> dict:
    init_db()
    db = get_session_factory()()
    try:
        return run_pipeline(db, source=source)
    finally:
        db.close()


def review_candidates() -> list[dict]:
    init_db()
    db = get_session_factory()()
    try:
        rows = VenueRepository(db).list_candidates()
        out = []
        for row in rows:
            if row.status not in {"new", "changed"}:
                continue
            out.append(
                {
                    "id": row.id,
                    "source": row.source,
                    "venue_id": row.venue_id,
                    "status": row.status,
                    "scraped_at": row.scraped_at.isoformat() if row.scraped_at else None,
                    "diff": json.loads(row.diff_json or "{}"),
                }
            )
        return out
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assiette distribution refresh worker")
    parser.add_argument("--source", default="all", choices=_SOURCES)
    parser.add_argument("--review", action="store_true", help="Print pending scrape candidates and exit")
    args = parser.parse_args()
    if args.review:
        print(review_candidates())
    else:
        print(run_refresh(args.source))
