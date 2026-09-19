"""Repository layer for venues and related tables."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session, joinedload

from backend.config import get_settings
from backend.models.orm import (
    DataSnapshot,
    QueryLog,
    RefreshRun,
    ScrapedCandidate,
    Venue,
    VenueSchedule,
    VenueVersion,
    VerificationLog,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def freshness_status(last_verified_at: datetime | None) -> str:
    if last_verified_at is None:
        return "stale"
    if last_verified_at.tzinfo is None:
        last_verified_at = last_verified_at.replace(tzinfo=timezone.utc)
    settings = get_settings()
    age_days = (_utcnow() - last_verified_at).days
    if age_days >= settings.freshness_refuse_days:
        return "refused"
    if age_days >= settings.freshness_warn_days:
        return "stale"
    return "fresh"


def venue_to_dict(venue: Venue) -> dict[str, Any]:
    return {
        "id": venue.id,
        "name": venue.name,
        "org": venue.org,
        "kind": venue.kind,
        "address": venue.address,
        "arrondissement": venue.arrondissement,
        "postal_code": venue.postal_code,
        "latitude": venue.latitude,
        "longitude": venue.longitude,
        "price_eur": venue.price_eur,
        "eligibility": venue.eligibility,
        "booking_required": venue.booking_required,
        "booking_url": venue.booking_url,
        "schedule": [
            {"weekday": s.weekday, "start": s.start_time, "end": s.end_time}
            for s in venue.schedules
        ],
        "notes": venue.notes,
        "french_hint": venue.french_hint,
        "last_verified": (
            venue.last_verified_at.date().isoformat() if venue.last_verified_at else ""
        ),
        "source_url": venue.source_url,
        "source": venue.source,
        "active": venue.active,
    }


class VenueRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active_distributions(self) -> list[dict[str, Any]]:
        stmt = (
            select(Venue)
            .options(joinedload(Venue.schedules))
            .where(Venue.active.is_(True), Venue.source == "distribution")
            .order_by(Venue.arrondissement, Venue.name)
        )
        venues = self.db.scalars(stmt).unique().all()
        return [venue_to_dict(v) for v in venues if freshness_status(v.last_verified_at) != "refused"]

    def list_active_venues(self) -> list[Venue]:
        stmt = (
            select(Venue)
            .options(joinedload(Venue.schedules))
            .where(Venue.active.is_(True))
            .order_by(Venue.arrondissement, Venue.name)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_venue(self, venue_id: str) -> Venue | None:
        stmt = select(Venue).options(joinedload(Venue.schedules)).where(Venue.id == venue_id)
        return self.db.scalars(stmt).unique().first()

    def upsert_venue(
        self,
        row: dict[str, Any],
        verifier: str = "refresh",
        commit: bool = True,
    ) -> tuple[Venue, list[str]]:
        venue = self.get_venue(row["id"])
        changed: list[str] = []
        verified_at = _utcnow()
        if row.get("last_verified"):
            try:
                verified_at = datetime.fromisoformat(row["last_verified"]).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        fields = {
            "source": row.get("source", "distribution"),
            "name": row["name"],
            "org": row.get("org", ""),
            "kind": row.get("kind", "distribution"),
            "address": row.get("address", ""),
            "arrondissement": row.get("arrondissement"),
            "postal_code": row.get("postal_code"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "price_eur": float(row.get("price_eur", 0)),
            "eligibility": row.get("eligibility", ""),
            "booking_required": bool(row.get("booking_required", False)),
            "booking_url": row.get("booking_url", ""),
            "source_url": row.get("source_url", ""),
            "french_hint": row.get("french_hint", ""),
            "notes": row.get("notes", ""),
            "active": True,
            "last_verified_at": verified_at,
        }

        if venue is None:
            venue = Venue(id=row["id"], **fields)
            self.db.add(venue)
            changed = list(fields.keys()) + ["schedule"]
        else:
            for key, value in fields.items():
                if getattr(venue, key) != value:
                    changed.append(key)
                    setattr(venue, key, value)
            venue.schedules.clear()
            self.db.flush()

        for slot in row.get("schedule") or []:
            venue.schedules.append(
                VenueSchedule(
                    weekday=slot["weekday"],
                    start_time=slot["start"],
                    end_time=slot["end"],
                )
            )

        if changed:
            self.db.add(
                VenueVersion(
                    venue_id=venue.id,
                    source_url=venue.source_url,
                    raw_payload=json.dumps(row, ensure_ascii=False),
                    changed_fields=json.dumps(changed),
                )
            )
            self.db.add(
                VerificationLog(
                    venue_id=venue.id,
                    verifier=verifier,
                    source_url=venue.source_url,
                    source_quote=row.get("notes", "")[:500],
                    notes=f"upsert changed: {', '.join(changed)}",
                )
            )

        if commit:
            self.db.commit()
            self.db.refresh(venue)
        return venue, changed

    def age_out_stale(self, refuse_days: int | None = None) -> int:
        days = refuse_days if refuse_days is not None else get_settings().freshness_refuse_days
        cutoff = _utcnow() - timedelta(days=days)
        stmt = select(Venue).where(Venue.active.is_(True), Venue.source == "distribution")
        deactivated = 0
        for venue in self.db.scalars(stmt):
            verified = venue.last_verified_at
            if verified is None:
                continue
            if verified.tzinfo is None:
                verified = verified.replace(tzinfo=timezone.utc)
            if verified < cutoff:
                venue.active = False
                deactivated += 1
        return deactivated

    def log_query(
        self,
        query_text: str,
        parsed_intent: dict[str, Any],
        result_count: int,
        engine: str,
        latency_ms: int,
        user_email: str | None = None,
        commit: bool = True,
    ) -> None:
        digest = hashlib.sha256(query_text.encode("utf-8")).hexdigest()
        self.db.add(
            QueryLog(
                query_text=query_text[:80],
                query_text_hash=digest,
                parsed_intent_json=json.dumps(parsed_intent, ensure_ascii=False),
                result_count=result_count,
                engine=engine,
                latency_ms=latency_ms,
                user_email=user_email,
            )
        )
        if commit:
            self.db.commit()

    def purge_query_logs(self, retain_days: int = 30) -> int:
        cutoff = _utcnow() - timedelta(days=retain_days)
        result = self.db.execute(delete(QueryLog).where(QueryLog.created_at < cutoff))
        return result.rowcount or 0

    def start_refresh(self, source: str = "all") -> RefreshRun:
        run = RefreshRun(source=source, status="running")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def running_refresh(self, within_minutes: int = 10) -> RefreshRun | None:
        cutoff = _utcnow() - timedelta(minutes=within_minutes)
        stmt = (
            select(RefreshRun)
            .where(RefreshRun.status == "running", RefreshRun.started_at >= cutoff)
            .order_by(desc(RefreshRun.started_at))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def finish_refresh(self, run_id: int, status: str, diff_summary: dict[str, Any]) -> RefreshRun:
        run = self.db.get(RefreshRun, run_id)
        if run is None:
            raise ValueError(f"refresh run {run_id} not found")
        run.status = status
        run.finished_at = _utcnow()
        run.diff_summary_json = json.dumps(diff_summary, ensure_ascii=False)
        self.db.commit()
        self.db.refresh(run)
        return run

    def last_refresh(self) -> RefreshRun | None:
        return self.db.scalars(select(RefreshRun).order_by(desc(RefreshRun.started_at)).limit(1)).first()

    def list_refresh_runs(self, limit: int = 8) -> list[RefreshRun]:
        stmt = select(RefreshRun).order_by(desc(RefreshRun.started_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_refresh(self, run_id: int) -> RefreshRun | None:
        return self.db.get(RefreshRun, run_id)

    def count_venues(self) -> int:
        return int(
            self.db.scalar(select(func.count()).select_from(Venue).where(Venue.active.is_(True))) or 0
        )

    def get_snapshot(self, key: str) -> DataSnapshot | None:
        return self.db.get(DataSnapshot, key)

    def put_snapshot(self, key: str, payload: Any, commit: bool = True) -> DataSnapshot:
        row = self.db.get(DataSnapshot, key)
        blob = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        if row is None:
            row = DataSnapshot(key=key, payload=blob, fetched_at=_utcnow())
            self.db.add(row)
        else:
            row.payload = blob
            row.fetched_at = _utcnow()
        if commit:
            self.db.commit()
        return row

    def data_version(self) -> str:
        last = self.last_refresh()
        stamp = last.finished_at.isoformat() if last and last.finished_at else "none"
        count = self.count_venues()
        raw = f"{last.id if last else 0}:{stamp}:{count}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def upsert_candidate(
        self,
        *,
        source: str,
        org: str,
        venue_id: str | None,
        parser_version: str,
        content_hash: str,
        payload: dict[str, Any],
        diff: dict[str, Any],
        status: str,
        commit: bool = False,
    ) -> ScrapedCandidate:
        pending = (
            select(ScrapedCandidate)
            .where(
                ScrapedCandidate.venue_id == venue_id,
                ScrapedCandidate.status.in_(("new", "changed", "unchanged")),
            )
            .order_by(desc(ScrapedCandidate.scraped_at))
            .limit(1)
        )
        existing = self.db.scalars(pending).first() if venue_id else None
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        diff_blob = json.dumps(diff, ensure_ascii=False)
        if existing is not None and existing.content_hash == content_hash:
            existing.scraped_at = _utcnow()
            existing.parser_version = parser_version
            existing.payload_json = blob
            existing.diff_json = diff_blob
            existing.status = "unchanged" if existing.status != "changed" else existing.status
            if commit:
                self.db.commit()
            return existing
        row = ScrapedCandidate(
            source=source,
            org=org,
            venue_id=venue_id,
            parser_version=parser_version,
            scraped_at=_utcnow(),
            content_hash=content_hash,
            payload_json=blob,
            diff_json=diff_blob,
            status=status,
        )
        self.db.add(row)
        if commit:
            self.db.commit()
            self.db.refresh(row)
        return row

    def list_candidates(self, status: str | None = None, limit: int = 50) -> list[ScrapedCandidate]:
        stmt = select(ScrapedCandidate).order_by(desc(ScrapedCandidate.scraped_at)).limit(limit)
        if status:
            stmt = stmt.where(ScrapedCandidate.status == status)
        return list(self.db.scalars(stmt).all())

    def count_pending_candidates(self) -> int:
        stmt = (
            select(func.count())
            .select_from(ScrapedCandidate)
            .where(ScrapedCandidate.status.in_(("new", "changed")))
        )
        return int(self.db.scalar(stmt) or 0)

    def get_candidate(self, candidate_id: int) -> ScrapedCandidate | None:
        return self.db.get(ScrapedCandidate, candidate_id)

    def approve_candidate(self, candidate_id: int, verifier: str = "review") -> Venue:
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"candidate {candidate_id} not found")
        payload = json.loads(candidate.payload_json or "{}")
        payload.pop("last_verified", None)
        payload["source"] = payload.get("source") or "distribution"
        if candidate.venue_id:
            payload["id"] = candidate.venue_id
        venue, _changed = self.upsert_venue(payload, verifier=f"human:{verifier}", commit=False)
        candidate.status = "approved"
        candidate.venue_id = venue.id
        self.db.commit()
        self.db.refresh(venue)
        return venue

    def reject_candidate(self, candidate_id: int) -> ScrapedCandidate:
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"candidate {candidate_id} not found")
        candidate.status = "rejected"
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
