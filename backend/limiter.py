"""Shared SlowAPI limiter."""

from __future__ import annotations

import time

from slowapi import Limiter

from assiette.cache import KEY_PREFIX, l2_incr
from backend.config import get_settings
from backend.observability import get_logger
from backend.security import client_ip

logger = get_logger("limiter")


def _storage_uri() -> str:
    uri = (get_settings().redis_url or "").strip()
    if not uri:
        # #region agent log
        from backend.debuglog import dbg

        dbg("backend/limiter.py:_storage_uri", "using_memory", {}, "B")
        # #endregion
        return "memory://"
    try:
        if uri.startswith(("redis://", "rediss://")):
            import redis  # noqa: F401
        # #region agent log
        from backend.debuglog import dbg

        dbg("backend/limiter.py:_storage_uri", "using_redis", {"scheme": uri.split(":", 1)[0]}, "B")
        # #endregion
        return uri
    except ImportError as exc:
        # #region agent log
        from backend.debuglog import dbg

        dbg("backend/limiter.py:_storage_uri", "redis_import_failed", {"error": str(exc)[:160]}, "B")
        # #endregion
        logger.warning("redis_limiter_unavailable", error=str(exc))
        return "memory://"


_settings = get_settings()
try:
    limiter = Limiter(
        key_func=client_ip,
        default_limits=[f"{_settings.rate_limit_per_minute}/minute"],
        storage_uri=_storage_uri(),
    )
except (ImportError, OSError, ValueError) as exc:
    logger.warning("redis_limiter_init_failed", error=str(exc))
    limiter = Limiter(
        key_func=client_ip,
        default_limits=[f"{_settings.rate_limit_per_minute}/minute"],
        storage_uri="memory://",
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
