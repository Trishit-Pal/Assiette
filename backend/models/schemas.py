"""Pydantic API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ScheduleSlot(BaseModel):
    weekday: str
    start: str
    end: str


class VenueOut(BaseModel):
    id: str
    source: str
    name: str
    org: str = ""
    kind: str = ""
    address: str = ""
    arrondissement: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_eur: float = 0.0
    eligibility: str = ""
    booking_required: bool = False
    booking_url: str = ""
    source_url: str = ""
    french_hint: str = ""
    notes: str = ""
    schedule: list[ScheduleSlot] = Field(default_factory=list)
    last_verified_at: datetime | None = None
    freshness_status: Literal["fresh", "stale", "refused"] = "fresh"

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    arrondissement: int | None = Field(default=None, ge=1, le=20)
    budget_eur: float | None = Field(default=None, ge=0, le=100)
    meal: Literal["breakfast", "lunch", "dinner", "any"] | None = None
    diet: Literal["any", "vegetarian", "vegan", "halal"] = "any"
    bursary: bool = False
    category: Literal["any", "crous", "distribution"] = "any"
    use_network: bool = True
    refresh: bool = False

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class ItineraryStop(BaseModel):
    id: str
    why: str = ""
    dietary_note: str = ""
    french_phrases: list[str] = Field(default_factory=list)


class MatchRecordOut(BaseModel):
    arrondissement: Literal["exact", "nearby", "unscoped"] = "unscoped"
    budget: Literal["ok", "unscoped"] = "unscoped"
    meal: Literal["open", "closed"] = "open"
    diet: Literal["match", "not_confirmed", "not_applicable"] = "not_applicable"


class EmptyReasonOut(BaseModel):
    reason: Literal["filters_too_strict", "no_data"]
    blocking_chips: list[Literal["budget", "arrondissement"]] = Field(default_factory=list)
    suggestion: Literal["relax_budget", "relax_arrondissement", "relax_both"] | None = None
    counts: dict[str, int] = Field(default_factory=dict)


class RankedPlaceOut(BaseModel):
    id: str
    source: str
    name: str
    org: str
    kind: str
    address: str
    arrondissement: int | None
    latitude: float | None
    longitude: float | None
    price_eur: float
    open_for_request: bool
    schedule_text: str
    eligibility: str
    menu_text: str
    booking_required: bool
    last_verified: str
    source_url: str
    french_hint: str
    notes: str
    score: float
    reasons: list[str] = Field(default_factory=list)
    freshness_status: str = "fresh"
    match: MatchRecordOut = Field(default_factory=MatchRecordOut)


class SourceMeta(BaseModel):
    name: str
    fetched_at: str | None = None
    mode: Literal["live", "cache", "stale", "snapshot"] = "cache"


class QueryResponse(BaseModel):
    summary: str
    stops: list[ItineraryStop]
    caveats: list[str] = Field(default_factory=list)
    engine: str
    intent: dict[str, Any]
    places: list[RankedPlaceOut]
    meta: dict[str, Any] = Field(default_factory=dict)
    refreshed_at: datetime | None = None
    offline_mode: bool = False
    data_version: str = ""
    generated_at: datetime | None = None
    sources: list[SourceMeta] = Field(default_factory=list)


class RetrieveResponse(BaseModel):
    places: list[RankedPlaceOut]
    meta: dict[str, Any] = Field(default_factory=dict)
    intent: dict[str, Any] = Field(default_factory=dict)
    data_version: str = ""
    generated_at: datetime | None = None
    sources: list[SourceMeta] = Field(default_factory=list)
    refreshed_at: datetime | None = None
    offline_mode: bool = False
    empty_reason: EmptyReasonOut | None = None


class ComposeRequest(BaseModel):
    query: str = Field(default="", max_length=500)
    intent: dict[str, Any] = Field(default_factory=dict)
    place_ids: list[str] = Field(default_factory=list)
    data_version: str | None = None
    use_network: bool = True


class ComposeResponse(BaseModel):
    summary: str
    stops: list[ItineraryStop]
    caveats: list[str] = Field(default_factory=list)
    engine: str
    meta: dict[str, Any] = Field(default_factory=dict)
    data_version: str = ""
    generated_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    database: str
    venue_count: int
    last_refresh: datetime | None = None


class AuthRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class AuthVerify(BaseModel):
    token: str = Field(..., min_length=10, max_length=256)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


class RefreshRequest(BaseModel):
    source: Literal["all", "crous", "distributions", "scrape"] = "all"


class RefreshAccepted(BaseModel):
    run_id: int
    status: str = "running"


class RefreshStatus(BaseModel):
    run_id: int
    status: str
    source: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    diff_summary: dict[str, Any] = Field(default_factory=dict)


class CandidateOut(BaseModel):
    id: int
    source: str
    org: str = ""
    venue_id: str | None = None
    parser_version: str = "v1"
    scraped_at: datetime | None = None
    content_hash: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    diff: dict[str, Any] = Field(default_factory=dict)
