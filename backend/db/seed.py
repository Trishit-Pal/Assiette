"""Seed venues from data/distributions.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db.session import get_session_factory, init_db
from backend.repo import VenueRepository
from assiette.paths import DISTRIBUTIONS_PATH


def seed_distributions() -> int:
    init_db()
    payload = json.loads(DISTRIBUTIONS_PATH.read_text(encoding="utf-8"))
    rows = payload.get("distributions") or []
    db = get_session_factory()()
    repo = VenueRepository(db)
    count = 0
    try:
        for row in rows:
            row = {**row, "source": "distribution"}
            repo.upsert_venue(row, verifier="seed")
            count += 1
    finally:
        db.close()
    return count


if __name__ == "__main__":
    n = seed_distributions()
    print(f"Seeded {n} distribution venues")
