"""Authenticated internal refresh trigger."""

from __future__ import annotations

import json
import secrets
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db.session import get_db
from backend.models.schemas import CandidateOut, RefreshAccepted, RefreshRequest, RefreshStatus
from backend.refresh.pipeline import run_pipeline
from backend.repo import VenueRepository

router = APIRouter(prefix="/internal", tags=["internal"])


def _refresh_auth(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().refresh_token
    if not expected or len(expected) < 32:
        raise HTTPException(status_code=404, detail="Not found")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    provided = authorization[7:].strip()
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid token")


def _run_in_background(run_id: int, source: str) -> None:
    from backend.db.session import get_session_factory

    db = get_session_factory()()
    try:
        run_pipeline(db, source=source, run_id=run_id)
    finally:
        db.close()


@router.post("/refresh", response_model=RefreshAccepted, status_code=202)
def trigger_refresh(
    body: RefreshRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(_refresh_auth),
) -> RefreshAccepted:
    repo = VenueRepository(db)
    running = repo.running_refresh(10)
    if running is not None:
        raise HTTPException(status_code=409, detail="A refresh is already running")
    run = repo.start_refresh(body.source)
    background.add_task(_run_in_background, run.id, body.source)
    return RefreshAccepted(run_id=run.id, status="running")


@router.get("/refresh/{run_id}", response_model=RefreshStatus)
def refresh_status(
    run_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(_refresh_auth),
) -> RefreshStatus:
    run = VenueRepository(db).get_refresh(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Refresh run not found")
    try:
        summary: dict[str, Any] = json.loads(run.diff_summary_json or "{}")
    except json.JSONDecodeError:
        summary = {}
    return RefreshStatus(
        run_id=run.id,
        status=run.status,
        source=run.source,
        started_at=run.started_at,
        finished_at=run.finished_at,
        diff_summary=summary,
    )


def _candidate_out(row) -> CandidateOut:
    try:
        payload = json.loads(row.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    try:
        diff = json.loads(row.diff_json or "{}")
    except json.JSONDecodeError:
        diff = {}
    return CandidateOut(
        id=row.id,
        source=row.source,
        org=row.org,
        venue_id=row.venue_id,
        parser_version=row.parser_version,
        scraped_at=row.scraped_at,
        content_hash=row.content_hash,
        status=row.status,
        payload=payload,
        diff=diff,
    )


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(_refresh_auth),
) -> list[CandidateOut]:
    return [_candidate_out(row) for row in VenueRepository(db).list_candidates(status=status)]


@router.post("/candidates/{candidate_id}/approve")
def approve_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(_refresh_auth),
) -> dict[str, str]:
    try:
        venue = VenueRepository(db).approve_candidate(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": venue.id, "status": "approved"}


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(_refresh_auth),
) -> dict[str, str]:
    try:
        row = VenueRepository(db).reject_candidate(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": str(row.id), "status": row.status}
