"""Refresh pipeline: warm CROUS cache, scrape candidates, re-verify distributions."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from assiette.cache import DATAV_KEY, LIST_HARD_TTL, LIST_KEY, cache_set, menu_key
from assiette.crous_client import CrousClient
from assiette.scrapers import SCRAPERS
from backend.refresh.parsers import PARSERS
from backend.repo import VenueRepository, venue_to_dict

MENU_RATE = 2.5
DROP_RATIO = 0.5


def run_pipeline(db: Session, source: str = "all", run_id: int | None = None) -> dict[str, Any]:
    repo = VenueRepository(db)
    run = repo.get_refresh(run_id) if run_id else repo.start_refresh(source)
    if run is None:
        run = repo.start_refresh(source)
    summary: dict[str, Any] = {"stages": {}, "updated": [], "unchanged": [], "errors": []}
    try:
        if source in {"all", "scrape"}:
            scrape = _scrape_sources(repo)
            summary["stages"]["scrape_sources"] = scrape
            if scrape.get("suspect"):
                summary["suspect"] = True
        if source in {"all", "crous"}:
            summary["stages"]["warm_crous"] = _warm_crous(repo)
        if source in {"all", "distributions"}:
            dist_source = "all" if source == "distributions" else source
            summary["stages"]["verify_distributions"] = _verify_distributions(repo, dist_source, summary)
            if summary.get("suspect"):
                summary["stages"]["age_out"] = {"deactivated": 0, "skipped": True}
            else:
                summary["stages"]["age_out"] = {"deactivated": repo.age_out_stale()}
        summary["stages"]["bump_version"] = _bump_version(repo)
        repo.purge_query_logs(30)
        db.commit()
        repo.finish_refresh(run.id, "completed", summary)
    except Exception as exc:
        summary["errors"].append({"stage": "pipeline", "error": str(exc)})
        try:
            repo.finish_refresh(run.id, "failed", summary)
        except Exception:
            pass
        raise
    return summary


def _payload_hash(row: dict[str, Any]) -> str:
    material = {
        "id": row.get("id"),
        "name": row.get("name"),
        "address": row.get("address"),
        "schedule": row.get("schedule") or [],
        "notes": row.get("notes"),
        "eligibility": row.get("eligibility"),
        "booking_url": row.get("booking_url"),
    }
    return hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _diff_live(repo: VenueRepository, row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    live = repo.get_venue(row["id"])
    if live is None:
        return "new", {"fields": ["*"]}
    current = venue_to_dict(live)
    changed: list[str] = []
    for key in ("name", "address", "notes", "eligibility", "booking_url"):
        if (current.get(key) or "") != (row.get(key) or ""):
            changed.append(key)
    live_sched = current.get("schedule") or []
    if live_sched != (row.get("schedule") or []):
        changed.append("schedule")
    if not changed:
        return "unchanged", {}
    return "changed", {"fields": changed}


def _scrape_sources(repo: VenueRepository) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    any_suspect = False
    for name, cls in SCRAPERS.items():
        scraper = cls()
        try:
            html = scraper.fetch()
        except Exception as exc:
            sources[name] = {"rows": 0, "error": str(exc), "suspect": True}
            any_suspect = True
            continue
        stamp = datetime.now(timezone.utc).date().isoformat()
        repo.put_snapshot(f"scrape:{name}:{stamp}", html, commit=False)
        rows = scraper.parse(html)
        meta_key = f"scrape:{name}:meta"
        prev = repo.get_snapshot(meta_key)
        prev_count = 0
        if prev and prev.payload:
            try:
                prev_count = int(json.loads(prev.payload).get("count") or 0)
            except (json.JSONDecodeError, TypeError, ValueError):
                prev_count = 0
        suspect = len(rows) == 0 or (prev_count > 0 and len(rows) < prev_count * DROP_RATIO)
        if suspect:
            any_suspect = True
        counts = {"new": 0, "changed": 0, "unchanged": 0}
        for row in rows:
            status, diff = _diff_live(repo, row)
            repo.upsert_candidate(
                source=scraper.source,
                org=scraper.org,
                venue_id=row.get("id"),
                parser_version=scraper.parser_version,
                content_hash=_payload_hash(row),
                payload=row,
                diff=diff,
                status=status,
                commit=False,
            )
            counts[status] = counts.get(status, 0) + 1
        repo.put_snapshot(meta_key, {"count": len(rows), "fetched_at": stamp, "suspect": suspect}, commit=False)
        sources[name] = {"rows": len(rows), "suspect": suspect, "fetched_at": stamp, **counts}
    return {"sources": sources, "suspect": any_suspect}


def _warm_crous(repo: VenueRepository) -> dict[str, Any]:
    client = CrousClient()
    rows, status = client.list_paris_restaurants(use_network=True)
    cache_set(LIST_KEY, {"data": rows, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, LIST_HARD_TTL)
    repo.put_snapshot("crous_list", {"data": rows, "status": status}, commit=False)
    warmed = 0
    errors = 0
    today = datetime.now()
    codes = [r.get("code") for r in rows if r.get("code")][:15]
    for code in codes:
        try:
            payload, menu_status = client.menu_for(int(code), date=today, use_network=True)
            if payload:
                stamp = today.strftime("%d-%m-%Y")
                cache_set(menu_key(int(code), stamp), payload, 20 * 60 * 60)
                warmed += 1
            elif "unavailable" in menu_status:
                errors += 1
        except Exception:
            errors += 1
        time.sleep(1.0 / MENU_RATE)
    return {"restaurants": len(rows), "menus_warmed": warmed, "errors": errors, "status": status}


def _verify_distributions(repo: VenueRepository, source: str, summary: dict[str, Any]) -> dict[str, Any]:
    parser = PARSERS.get(source, PARSERS["all"])
    rows = parser() if callable(parser) else []
    updated = 0
    unchanged = 0
    for row in rows:
        try:
            row = {**row, "source": row.get("source") or "distribution"}
            _venue, changed = repo.upsert_venue(row, verifier=f"refresh:{source}", commit=False)
            if changed:
                updated += 1
                summary["updated"].append({"id": row.get("id"), "changed": changed})
            else:
                unchanged += 1
                summary["unchanged"].append(row.get("id"))
        except Exception as exc:
            summary["errors"].append({"id": row.get("id"), "error": str(exc)})
    return {"rows": len(rows), "updated": updated, "unchanged": unchanged}


def _bump_version(repo: VenueRepository) -> dict[str, Any]:
    version = repo.data_version()
    cache_set(DATAV_KEY, version, 24 * 60 * 60)
    return {"data_version": version}
