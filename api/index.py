"""Vercel Python entrypoint. Re-exports the FastAPI ASGI app."""

from __future__ import annotations

from backend.debuglog import dbg

# #region agent log
dbg("api/index.py:import", "vercel_entry_start", {}, "C")
# #endregion

try:
    from backend.api import app

    # #region agent log
    dbg("api/index.py:ok", "backend_api_imported", {"app": type(app).__name__}, "C")
    # #endregion
except Exception as exc:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    # #region agent log
    dbg(
        "api/index.py:fail",
        "backend_api_import_failed",
        {"error_type": type(exc).__name__, "error": str(exc)[:240]},
        "A",
    )
    # #endregion

    app = FastAPI(title="Assiette boot failure")

    @app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
    def _boot_failed(path: str = "") -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "status": "boot_error",
                "error_type": type(exc).__name__,
                "error": str(exc)[:300],
            },
        )

__all__ = ["app"]
