"""Query orchestration: retrieve, then generate. /query stays a wrapper."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from assiette.llm import GroqLLM, generate_itinerary
from assiette.retrieval import DISPLAY_LIMIT, RankedPlace
from backend.models.schemas import (
    ComposeRequest,
    ComposeResponse,
    EmptyReasonOut,
    ItineraryStop,
    QueryRequest,
    QueryResponse,
    RankedPlaceOut,
    RetrieveResponse,
    SourceMeta,
)
from backend.observability import get_logger
from backend.repo import VenueRepository
from backend.services.retrieval_service import (
    current_data_version,
    intent_from_payload,
    place_to_out,
    ranked_from_cached,
    retrieve_places,
)

logger = get_logger("query_service")


def _as_places(payload: dict[str, Any]) -> list[RankedPlace]:
    places = payload.get("places") or []
    if places and isinstance(places[0], RankedPlace):
        return places
    return ranked_from_cached(places)


def _as_place_outs(payload: dict[str, Any]) -> list[RankedPlaceOut]:
    places = payload.get("places") or []
    if places and isinstance(places[0], RankedPlace):
        return [place_to_out(p) for p in places[:DISPLAY_LIMIT]]
    return [RankedPlaceOut.model_validate(p) for p in places[:DISPLAY_LIMIT]]


def _sources(payload: dict[str, Any]) -> list[SourceMeta]:
    rows = payload.get("sources") or []
    out: list[SourceMeta] = []
    for row in rows:
        if isinstance(row, SourceMeta):
            out.append(row)
        else:
            out.append(SourceMeta.model_validate(row))
    return out


def retrieve_response(db: Session, req: QueryRequest, *, parse_query: bool = True) -> tuple[RetrieveResponse, dict[str, Any]]:
    payload = retrieve_places(db, req, parse_query=parse_query)
    generated = payload.get("generated_at")
    if isinstance(generated, str):
        generated = datetime.fromisoformat(generated)
    empty = payload.get("empty_reason")
    if isinstance(empty, dict):
        empty = EmptyReasonOut.model_validate(empty)
    body = RetrieveResponse(
        places=_as_place_outs(payload),
        meta=payload.get("meta") or {},
        intent=payload["intent"].__dict__ if hasattr(payload.get("intent"), "__dict__") else (payload.get("intent") or {}),
        data_version=payload.get("data_version") or "",
        generated_at=generated or datetime.now(timezone.utc),
        sources=_sources(payload),
        refreshed_at=payload.get("refreshed_at"),
        offline_mode=bool(payload.get("offline_mode")),
        empty_reason=empty,
    )
    return body, payload


def compose_itinerary(db: Session, req: ComposeRequest) -> ComposeResponse:
    meal_raw = req.intent.get("meal")
    diet_raw = req.intent.get("diet") or "any"
    cat_raw = req.intent.get("category") or "any"
    query_req = QueryRequest(
        query=req.query or str(req.intent.get("query") or "meal"),
        arrondissement=req.intent.get("arrondissement"),
        budget_eur=req.intent.get("budget_eur"),
        meal=meal_raw if meal_raw in {"breakfast", "lunch", "dinner", "any"} else None,
        diet=diet_raw if diet_raw in {"any", "vegetarian", "vegan", "halal"} else "any",
        bursary=bool(req.intent.get("bursary")),
        category=cat_raw if cat_raw in {"any", "crous", "distribution"} else "any",
        use_network=req.use_network,
    )
    retrieved, payload = retrieve_response(db, query_req, parse_query=False)
    candidates = _as_places(payload)
    allowed = {p.id: p for p in candidates}
    chosen = [allowed[i] for i in req.place_ids if i in allowed]
    intent = payload.get("intent")
    if not hasattr(intent, "query"):
        intent = intent_from_payload(req.intent or retrieved.intent, query_req.query)
    knowledge = (payload.get("meta") or {}).get("knowledge") or []
    itinerary = generate_itinerary(intent, chosen, knowledge, GroqLLM())
    version = retrieved.data_version
    version_drift = bool(req.data_version and req.data_version != version)
    meta = dict(retrieved.meta)
    if version_drift:
        meta["version_drift"] = True
    return ComposeResponse(
        summary=itinerary.get("summary", ""),
        stops=[ItineraryStop(**s) for s in itinerary.get("stops") or []],
        caveats=itinerary.get("caveats") or [],
        engine=itinerary.get("engine", "template"),
        meta=meta,
        data_version=version,
        generated_at=datetime.now(timezone.utc),
    )


def run_query(db: Session, req: QueryRequest) -> QueryResponse:
    start = time.perf_counter()
    retrieved, payload = retrieve_response(db, req)
    places = _as_places(payload)
    intent = payload.get("intent")
    if not hasattr(intent, "query"):
        intent = intent_from_payload(retrieved.intent, req.query)
    knowledge = (payload.get("meta") or {}).get("knowledge") or []
    itinerary = generate_itinerary(intent, places, knowledge, GroqLLM())
    latency_ms = int((time.perf_counter() - start) * 1000)

    try:
        from backend.db.session import get_session_factory

        intent_payload = intent.__dict__
        query_text = req.query
        result_count = len(itinerary.get("stops") or [])
        engine = itinerary.get("engine", "unknown")

        def _log() -> None:
            session = get_session_factory()()
            try:
                VenueRepository(session).log_query(
                    query_text=query_text,
                    parsed_intent=intent_payload,
                    result_count=result_count,
                    engine=engine,
                    latency_ms=latency_ms,
                )
            except Exception:
                logger.warning("query_log_failed")
            finally:
                session.close()

        import threading

        threading.Thread(target=_log, daemon=True).start()
    except Exception:
        logger.warning("query_log_failed")

    logger.info(
        "query_completed",
        result_count=len(itinerary.get("stops") or []),
        engine=itinerary.get("engine"),
        latency_ms=latency_ms,
        offline_mode=retrieved.offline_mode,
    )

    return QueryResponse(
        summary=itinerary.get("summary", ""),
        stops=[ItineraryStop(**s) for s in itinerary.get("stops") or []],
        caveats=itinerary.get("caveats") or [],
        engine=itinerary.get("engine", "template"),
        intent=intent.__dict__,
        places=retrieved.places,
        meta=retrieved.meta,
        refreshed_at=retrieved.refreshed_at,
        offline_mode=retrieved.offline_mode,
        data_version=retrieved.data_version or current_data_version(db),
        generated_at=datetime.now(timezone.utc),
        sources=retrieved.sources,
    )
