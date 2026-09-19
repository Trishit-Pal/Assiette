"""Tiny NDJSON debug logger for Vercel boot diagnosis. Do not log secrets."""

from __future__ import annotations

import json
import time
from pathlib import Path

_PATHS = (
    Path("debug-7ba650.log"),
    Path(__file__).resolve().parents[1] / "debug-7ba650.log",
    Path("/tmp/debug-7ba650.log"),
)


def dbg(location: str, message: str, data: dict, hypothesis_id: str, run_id: str = "pre-fix") -> None:
    rec = {
        "sessionId": "7ba650",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "hypothesisId": hypothesis_id,
        "runId": run_id,
    }
    line = json.dumps(rec, default=str) + "\n"
    for path in _PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
            return
        except OSError:
            continue
