"""Minimal circuit breaker with L2-shared state and in-process fallback."""

from __future__ import annotations

import time
from typing import Literal

from assiette.cache import KEY_PREFIX, cache_get, cache_set

FAILURE_THRESHOLD = 5
OPEN_SECONDS = 60.0
HARD_TTL = 5 * 60

State = Literal["closed", "open", "half_open"]


def _key(service: str) -> str:
    return f"{KEY_PREFIX}:cb:{service}"


def _default() -> dict:
    return {"failures": 0, "opened_at": 0.0, "state": "closed"}


def _load(service: str) -> dict:
    hit = cache_get(_key(service), HARD_TTL)
    if hit is None:
        return _default()
    value, _age, _tier = hit
    if not isinstance(value, dict):
        return _default()
    return {**_default(), **value}


def _store(service: str, payload: dict) -> None:
    cache_set(_key(service), payload, HARD_TTL)


def allow_request(service: str) -> bool:
    row = _load(service)
    state: State = row.get("state") or "closed"
    if state == "closed":
        return True
    opened_at = float(row.get("opened_at") or 0)
    if time.time() - opened_at >= OPEN_SECONDS:
        row["state"] = "half_open"
        _store(service, row)
        return True
    return False


def record_success(service: str) -> None:
    _store(service, _default())


def record_failure(service: str) -> None:
    row = _load(service)
    failures = int(row.get("failures") or 0) + 1
    if failures >= FAILURE_THRESHOLD or row.get("state") == "half_open":
        _store(service, {"failures": failures, "opened_at": time.time(), "state": "open"})
        return
    row["failures"] = failures
    _store(service, row)


def current_state(service: str) -> State:
    return _load(service).get("state") or "closed"  # type: ignore[return-value]
