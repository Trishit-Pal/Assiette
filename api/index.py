"""Vercel Python entrypoint. Re-exports the FastAPI ASGI app."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.debuglog import dbg

# #region agent log
dbg("api/index.py:import", "vercel_entry_start", {}, "C")
# #endregion

# Top-level FastAPI() is required for Vercel to detect this file as a function.
app = FastAPI(title="Assiette")

try:
    from backend.api import app as _app

    app = _app
    # #region agent log
    dbg("api/index.py:ok", "backend_api_imported", {"app": type(app).__name__}, "C")
    # #endregion
except Exception as exc:
    error_type = type(exc).__name__
    error_text = str(exc)[:300]
    # #region agent log
    dbg(
        "api/index.py:fail",
        "backend_api_import_failed",
        {"error_type": error_type, "error": error_text[:240]},
        "A",
    )
    # #endregion

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
