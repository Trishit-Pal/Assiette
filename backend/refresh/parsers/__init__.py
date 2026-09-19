"""Refresh worker parsers — source of truth is data/distributions.json."""

from __future__ import annotations

import json

from assiette.paths import DISTRIBUTIONS_PATH

SOURCES = ("linkee", "cop1", "restos", "secours", "ordre_malte", "all")


def load_rows(source: str = "all") -> list[dict]:
    payload = json.loads(DISTRIBUTIONS_PATH.read_text(encoding="utf-8"))
    rows = [{**row, "source": "distribution"} for row in payload.get("distributions") or []]
    if source == "all":
        return rows
    key = source.lower()
    return [
        row
        for row in rows
        if key in (row.get("org") or "").lower() or key in (row.get("id") or "").lower()
    ]


PARSERS = {name: (lambda n=name: load_rows(n)) for name in SOURCES}
