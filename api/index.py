"""Vercel Python entrypoint. Re-exports the FastAPI ASGI app."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Top-level FastAPI() is required for Vercel to detect this file as a function.
app = FastAPI(title="Assiette")

try:
    from backend.api import app as _app

    app = _app
except Exception as exc:
    error_type = type(exc).__name__
    error_text = str(exc)[:300]

    # Bind error_* as defaults: `except as exc` is cleared when the block ends.
    @app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
    def _boot_failed(path: str = "", err_type: str = error_type, err_text: str = error_text) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "status": "boot_error",
                "error_type": err_type,
                "error": err_text,
            },
        )

__all__ = ["app"]
