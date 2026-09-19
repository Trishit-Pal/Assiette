"""Database engine and session factory."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from backend.config import get_settings
from backend.models.orm import Base


def _is_postgres(url: str) -> bool:
    return url.startswith("postgres")


def _normalise_database_url(url: str) -> str:
    url = (url or "").strip()
    if not _is_postgres(url):
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    scheme, sep, rest = url.partition("://")
    if sep and scheme in {"postgresql", "postgres"}:
        url = f"postgresql+psycopg2://{rest}"
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "channel_binding"]
    return urlunparse(parsed._replace(query=urlencode(query)))


def _ensure_neon_pooler(url: str) -> str:
    """Prefer Neon's transaction-pooler host so serverless does not exhaust connections."""
    if "neon.tech" not in url or "-pooler" in url:
        return url
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host.endswith(".neon.tech") or "-pooler." in host:
        return url
    labels = host.split(".")
    labels[0] = f"{labels[0]}-pooler"
    netloc = parsed.netloc.replace(host, ".".join(labels), 1)
    return urlunparse(parsed._replace(netloc=netloc))


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = _normalise_database_url(settings.database_url)
    if _is_postgres(url):
        url = _ensure_neon_pooler(url)
        connect_args: dict[str, object] = {"connect_timeout": 5}
        if "+psycopg://" in url:
            connect_args["prepare_threshold"] = 0
        return create_engine(
            url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return create_engine(
        url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
