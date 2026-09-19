"""Vercel Python entrypoint. Re-exports the FastAPI ASGI app."""

from backend.api import app

__all__ = ["app"]
