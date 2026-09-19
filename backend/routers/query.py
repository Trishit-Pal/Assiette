"""Query, retrieve, compose, and venue read routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.limiter import limiter
from backend.models.orm import Venue
from backend.models.schemas import (
    ComposeRequest,
    ComposeResponse,
    QueryRequest,
    QueryResponse,
    RetrieveResponse,
    VenueOut,
)
from backend.observability import get_logger
from backend.repo import VenueRepository, freshness_status, venue_to_dict
from backend.services.query_service import (
    compose_itinerary,
    retrieve_response,
    run_query,
)
from backend.services.retrieval_service import (
    current_data_version,
    intent_from_request,
    intent_hash,
)

router = APIRouter()
logger = get_logger("query")


def _http_date(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return format_datetime(value)


def _etag_match(incoming: str | None, etag: str) -> bool:
    if not incoming:
        return False
    left = incoming.strip().removeprefix("W/").strip()
    right = etag.strip().removeprefix("W/").strip()
    return left == right


def _apply_cache_headers(request: Request, response: Response, etag: str, last_modified: datetime | None) -> Response | None:
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=600"
    stamped = _http_date(last_modified)
    if stamped:
        response.headers["Last-Modified"] = stamped
    if _etag_match(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers=dict(response.headers))
    return None


@router.get("/retrieve", response_model=RetrieveResponse)
@limiter.limit("60/minute")
def retrieve(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=1, max_length=500),
    arrondissement: int | None = Query(default=None, ge=1, le=20),
    budget_eur: float | None = Query(default=None, ge=0, le=100),
    meal: str | None = Query(default=None),
    diet: str = Query(default="any"),
    bursary: bool = False,
    category: str = Query(default="any"),
    use_network: bool = True,
    refresh: bool = False,
    db: Session = Depends(get_db),
) -> RetrieveResponse | Response:
    req = QueryRequest(
        query=q,
        arrondissement=arrondissement,
        budget_eur=budget_eur,
        meal=meal,  # type: ignore[arg-type]
        diet=diet,  # type: ignore[arg-type]
        bursary=bursary,
        category=category,  # type: ignore[arg-type]
        use_network=use_network,
        refresh=refresh,
    )
    try:
        hashed = intent_hash(intent_from_request(req, parse_query=False))
        version = current_data_version(db)
        etag = f'W/"{version}:{hashed}"'
        last = VenueRepository(db).last_refresh()
        if refresh:
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "no-store"
        else:
            not_modified = _apply_cache_headers(request, response, etag, last.finished_at if last else None)
            if not_modified is not None:
                return not_modified
        body, _payload = retrieve_response(db, req, parse_query=False)
        return body
    except SQLAlchemyError as exc:
        logger.warning("retrieve_db_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.post("/compose", response_model=ComposeResponse)
@limiter.limit("10/minute")
def compose(req: ComposeRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> ComposeResponse:
    response.headers["Cache-Control"] = "no-store"
    return compose_itinerary(db, req)


@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
def query(req: QueryRequest, request: Request, db: Session = Depends(get_db)) -> QueryResponse:
    return run_query(db, req)


def _venue_out(venue: Venue) -> VenueOut:
    data = venue_to_dict(venue)
    return VenueOut(
        id=venue.id,
        source=venue.source,
        name=venue.name,
        org=venue.org,
        kind=venue.kind,
        address=venue.address,
        arrondissement=venue.arrondissement,
        latitude=venue.latitude,
        longitude=venue.longitude,
        price_eur=venue.price_eur,
        eligibility=venue.eligibility,
        booking_required=venue.booking_required,
        booking_url=venue.booking_url,
        source_url=venue.source_url,
        french_hint=venue.french_hint,
        notes=venue.notes,
        schedule=data["schedule"],
        last_verified_at=venue.last_verified_at,
        freshness_status=freshness_status(venue.last_verified_at),  # type: ignore[arg-type]
    )


@router.get("/venues", response_model=list[VenueOut])
def list_venues(request: Request, response: Response, db: Session = Depends(get_db)) -> list[VenueOut] | Response:
    repo = VenueRepository(db)
    venues = [_venue_out(v) for v in repo.list_active_venues() if freshness_status(v.last_verified_at) != "refused"]
    last = repo.last_refresh()
    version = repo.data_version()
    etag = f'W/"{version}:venues"'
    not_modified = _apply_cache_headers(request, response, etag, last.finished_at if last else None)
    if not_modified is not None:
        return not_modified
    return venues


@router.get("/venues/{venue_id}", response_model=VenueOut)
def get_venue(venue_id: str, db: Session = Depends(get_db)) -> VenueOut:
    venue = VenueRepository(db).get_venue(venue_id)
    if venue is None or not venue.active:
        raise HTTPException(status_code=404, detail="Venue not found")
    return _venue_out(venue)


@router.get("/refresh-runs")
def refresh_runs(db: Session = Depends(get_db)) -> dict:
    repo = VenueRepository(db)
    rows = repo.list_refresh_runs()
    out = []
    for row in rows:
        try:
            summary = json.loads(row.diff_summary_json or "{}")
        except json.JSONDecodeError:
            summary = {}
        out.append(
            {
                "id": row.id,
                "source": row.source,
                "status": row.status,
                "started_at": row.started_at,
                "finished_at": row.finished_at,
                "diff_summary": summary,
            }
        )
    scrape_health = []
    for run in out:
        stage = (run.get("diff_summary") or {}).get("stages", {}).get("scrape_sources") or {}
        sources = stage.get("sources") or {}
        if sources:
            for name, info in sources.items():
                scrape_health.append(
                    {
                        "source": name,
                        "rows": info.get("rows"),
                        "suspect": bool(info.get("suspect") or stage.get("suspect")),
                        "fetched_at": info.get("fetched_at"),
                    }
                )
            break
    return {
        "runs": out,
        "pending_candidates": repo.count_pending_candidates(),
        "scrape_health": scrape_health,
    }
