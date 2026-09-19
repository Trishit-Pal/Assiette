"""Structured logging and optional Sentry."""

from __future__ import annotations

import logging

import structlog

from backend.config import get_settings


def configure_observability() -> None:
    settings = get_settings()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        except ImportError:
            pass


def get_logger(name: str = "assiette"):
    return structlog.get_logger(name)
