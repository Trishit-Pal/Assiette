"""Layered cache: L1 in-process LRU, L2 Upstash REST, L3 durable snapshot."""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Any, Callable

import requests

from backend.config import get_settings
from backend.observability import get_logger

log = get_logger("cache")

CACHE_VERSION = "v1"
KEY_PREFIX = f"a:{CACHE_VERSION}"

LIST_SOFT_TTL = 30 * 60
LIST_HARD_TTL = 24 * 60 * 60
MENU_SOFT_TTL = 6 * 60 * 60
MENU_HARD_TTL = 20 * 60 * 60
MENU404_TTL = 6 * 60 * 60
DIST_SOFT_TTL = 10 * 60
DIST_HARD_TTL = 60 * 60
RETR_SOFT_TTL = 5 * 60
RETR_HARD_TTL = 15 * 60

LIST_KEY = f"{KEY_PREFIX}:crous:list:r22"
DATAV_KEY = f"{KEY_PREFIX}:datav"

_L1_MAX = 256
_KV_TIMEOUT = 0.3


def menu_key(code: int, stamp: str) -> str:
    return f"{KEY_PREFIX}:crous:menu:{code}:{stamp}"


def menu404_key(code: int, stamp: str) -> str:
    return f"{KEY_PREFIX}:crous:menu404:{code}:{stamp}"


def dist_key(data_version: str) -> str:
    return f"{KEY_PREFIX}:dist:{data_version}"


def retr_key(data_version: str, intent_hash: str) -> str:
    return f"{KEY_PREFIX}:retr:{data_version}:{intent_hash}"


class _L1:
    def __init__(self, maxsize: int = _L1_MAX) -> None:
        self._maxsize = maxsize
        self._data: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> tuple[Any, float] | None:
        with self._lock:
            row = self._data.get(key)
            if row is None:
                return None
            self._data.move_to_end(key)
            return row

    def set(self, key: str, value: Any, stored_at: float | None = None) -> None:
        stored_at = stored_at if stored_at is not None else time.time()
        with self._lock:
            self._data[key] = (value, stored_at)
            self._data.move_to_end(key)
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


_l1 = _L1()
_revalidating: set[str] = set()
_revalidating_lock = threading.Lock()


def _envelope(value: Any, stored_at: float) -> str:
    return json.dumps({"v": value, "t": stored_at}, ensure_ascii=False, default=str)


def _unwrap(raw: Any) -> tuple[Any, float] | None:
    if raw is None:
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return raw, time.time()
    elif isinstance(raw, dict):
        payload = raw
    else:
        return raw, time.time()
    if isinstance(payload, dict) and "v" in payload and "t" in payload:
        return payload["v"], float(payload["t"])
    return payload, time.time()


def _upstash_configured() -> bool:
    settings = get_settings()
    return bool(settings.upstash_redis_rest_url and settings.upstash_redis_rest_token)


def _upstash(command: list[str]) -> Any | None:
    if not _upstash_configured():
        return None
    settings = get_settings()
    url = settings.upstash_redis_rest_url.rstrip("/")
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.upstash_redis_rest_token}",
                "Content-Type": "application/json",
            },
            json=command,
            timeout=_KV_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("result")
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.warning("upstash_failed", error=str(exc), command=command[0] if command else "")
        return None


def l2_get(key: str) -> tuple[Any, float] | None:
    result = _upstash(["GET", key])
    return _unwrap(result)


def l2_set(key: str, value: Any, ttl: int, stored_at: float | None = None) -> None:
    stored_at = stored_at if stored_at is not None else time.time()
    _upstash(["SET", key, _envelope(value, stored_at), "EX", str(max(1, int(ttl)))])


def l2_delete(key: str) -> None:
    _upstash(["DEL", key])


def l2_incr(key: str, ttl: int) -> int | None:
    result = _upstash(["INCR", key])
    if result is None:
        return None
    _upstash(["EXPIRE", key, str(max(1, int(ttl)))])
    try:
        return int(result)
    except (TypeError, ValueError):
        return None


def cache_get(key: str, hard_ttl: int) -> tuple[Any, float, str] | None:
    """Return (value, age_seconds, tier) if present and inside hard TTL."""
    now = time.time()
    l1 = _l1.get(key)
    if l1 is not None:
        value, stored_at = l1
        age = now - stored_at
        if age <= hard_ttl:
            return value, age, "l1"
        _l1.delete(key)
    l2 = l2_get(key)
    if l2 is not None:
        value, stored_at = l2
        age = now - stored_at
        if age <= hard_ttl:
            _l1.set(key, value, stored_at)
            return value, age, "l2"
    return None


def cache_set(key: str, value: Any, hard_ttl: int) -> None:
    stored_at = time.time()
    _l1.set(key, value, stored_at)
    l2_set(key, value, hard_ttl, stored_at)


def begin_revalidate(key: str) -> bool:
    with _revalidating_lock:
        if key in _revalidating:
            return False
        _revalidating.add(key)
        return True


def end_revalidate(key: str) -> None:
    with _revalidating_lock:
        _revalidating.discard(key)


def get_or_load(
    key: str,
    *,
    soft_ttl: int,
    hard_ttl: int,
    loader: Callable[[], Any],
    background: Callable[[Callable[[], None]], None] | None = None,
) -> tuple[Any, float, str, bool]:
    """Fetch with stale-while-revalidate. Returns (value, age, tier, stale)."""
    hit = cache_get(key, hard_ttl)
    if hit is not None:
        value, age, tier = hit
        stale = age > soft_ttl
        if stale and begin_revalidate(key):

            def _refresh() -> None:
                try:
                    fresh = loader()
                    cache_set(key, fresh, hard_ttl)
                except Exception as exc:
                    log.warning("revalidate_failed", key=key, error=str(exc))
                finally:
                    end_revalidate(key)

            if background is not None:
                background(_refresh)
            else:
                threading.Thread(target=_refresh, daemon=True).start()
        return value, age, tier, stale
    value = loader()
    cache_set(key, value, hard_ttl)
    return value, 0.0, "live", False


def clear_l1() -> None:
    _l1.clear()
