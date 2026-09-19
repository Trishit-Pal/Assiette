"""Assiette FastAPI service."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.types import Scope

from backend.auth import create_session_token, request_magic_link, require_user, verify_magic_link
from backend.config import get_settings
from backend.db.session import get_db, get_session_factory, init_db
from backend.limiter import limiter
from backend.models.orm import User
from backend.models.schemas import AuthRequest, AuthResponse, AuthVerify, HealthResponse
from backend.observability import configure_observability, get_logger
from backend.repo import VenueRepository
from backend.routers import admin as admin_router
from backend.routers import query as query_router

configure_observability()
logger = get_logger("api")
settings = get_settings()


class HashedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if path.endswith("index.html") or path in {"", "."}:
            response.headers["Cache-Control"] = "no-cache"
        elif "/assets/" in path or path.endswith((".js", ".css", ".woff2")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    auto = settings.auto_init_db or os.environ.get("ASSIETTE_AUTO_INIT_DB") == "1"
    if auto:
        init_db()
        try:
            from backend.db.seed import seed_distributions

            seed_distributions()
        except Exception as exc:
            logger.warning("seed_skipped", error=str(exc))
    else:
        try:
            db = get_session_factory()()
            db.execute(text("SELECT 1"))
            count = VenueRepository(db).count_venues()
            if count == 0:
                logger.warning("venues_empty")
            db.close()
        except Exception as exc:
            logger.warning("db_not_ready", error=str(exc))
    yield


app = FastAPI(title="Assiette API", version="3.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=bool(settings.cors_origin_list),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "If-None-Match"],
)

app.include_router(query_router.router)
if settings.refresh_token and len(settings.refresh_token) >= 32:
    app.include_router(admin_router.router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Content-Security-Policy"] = settings.csp_policy
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    repo = VenueRepository(db)
    try:
        last = repo.last_refresh()
        count = repo.count_venues()
        db_status = "ok"
    except Exception:
        last = None
        count = 0
        db_status = "error"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        venue_count=count,
        last_refresh=last.finished_at if last else None,
    )


@app.post("/auth/request")
@limiter.limit("5/minute")
def auth_request(req: AuthRequest, request: Request, db: Session = Depends(get_db)):
    from backend.limiter import email_auth_allowed

    if not email_auth_allowed(req.email):
        payload: dict[str, str] = {"message": "If that address is eligible, a sign-in link is on its way."}
        return payload
    token = request_magic_link(db, req.email)
    payload: dict[str, str] = {"message": "If that address is eligible, a sign-in link is on its way."}
    if token and not settings.is_production and not settings.smtp_host and not settings.resend_api_key:
        payload["dev_token"] = token
    return payload


@app.post("/auth/verify", response_model=AuthResponse)
def auth_verify(req: AuthVerify, db: Session = Depends(get_db)) -> AuthResponse:
    user = verify_magic_link(db, req.token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return AuthResponse(access_token=create_session_token(user), email=user.email)


@app.get("/auth/me")
def auth_me(user: User = Depends(require_user)) -> dict[str, str]:
    return {"email": user.email, "role": user.role}


DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
INDEX = DIST / "index.html"


def _spa_index() -> FileResponse:
    if not INDEX.is_file():
        raise HTTPException(status_code=404, detail="Frontend not built — run npm --prefix frontend run build")
    response = FileResponse(INDEX)
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/about")
@app.get("/signin")
def spa_pages() -> FileResponse:
    return _spa_index()


if settings.serve_frontend and DIST.is_dir() and not settings.is_production:
    app.mount("/", HashedStaticFiles(directory=str(DIST), html=True), name="spa")
