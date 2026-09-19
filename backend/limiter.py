"""Shared SlowAPI limiter."""

from __future__ import annotations

import time

from slowapi import Limiter

from assiette.cache import KEY_PREFIX, l2_incr
from backend.config import get_settings
from backend.security import client_ip

_settings = get_settings()
limiter = Limiter(
    key_func=client_ip,
    default_limits=[f"{_settings.rate_limit_per_minute}/minute"],
    storage_uri=_settings.redis_url or "memory://",
)

_EMAIL_HITS: dict[str, list[float]] = {}
_EMAIL_LIMIT = 5
_EMAIL_WINDOW = 60


def email_auth_allowed(email: str) -> bool:
    """At most 5 magic-link requests per email per minute (L2, then in-process)."""
    normalised = email.strip().lower()
    if not normalised:
        return False
    key = f"{KEY_PREFIX}:rl:auth:{normalised}"
    count = l2_incr(key, _EMAIL_WINDOW)
    if count is not None:
        return count <= _EMAIL_LIMIT
    now = time.time()
    hits = [stamp for stamp in _EMAIL_HITS.get(normalised, []) if now - stamp < _EMAIL_WINDOW]
    hits.append(now)
    _EMAIL_HITS[normalised] = hits
    return len(hits) <= _EMAIL_LIMIT
