"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org: Mapped[str] = mapped_column(String(255), default="")
    kind: Mapped[str] = mapped_column(String(64), default="distribution")
    address: Mapped[str] = mapped_column(String(512), default="")
    arrondissement: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    postal_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_eur: Mapped[float] = mapped_column(Float, default=0.0)
    eligibility: Mapped[str] = mapped_column(Text, default="")
    booking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    booking_url: Mapped[str] = mapped_column(String(512), default="")
    source_url: Mapped[str] = mapped_column(String(512), default="")
    french_hint: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_venues_source_active_arr", "source", "active", "arrondissement"),)

    schedules: Mapped[list[VenueSchedule]] = relationship(back_populates="venue", cascade="all, delete-orphan")
    versions: Mapped[list[VenueVersion]] = relationship(back_populates="venue", cascade="all, delete-orphan")
    verifications: Mapped[list[VerificationLog]] = relationship(back_populates="venue", cascade="all, delete-orphan")


class VenueSchedule(Base):
    __tablename__ = "venue_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[str] = mapped_column(String(16), nullable=False)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)

    venue: Mapped[Venue] = relationship(back_populates="schedules")


class VenueVersion(Base):
    __tablename__ = "venue_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_url: Mapped[str] = mapped_column(String(512), default="")
    source_screenshot_hash: Mapped[str] = mapped_column(String(64), default="")
    raw_payload: Mapped[str] = mapped_column(Text, default="")
    changed_fields: Mapped[str] = mapped_column(Text, default="")

    venue: Mapped[Venue] = relationship(back_populates="versions")


class VerificationLog(Base):
    __tablename__ = "verification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    verifier: Mapped[str] = mapped_column(String(128), default="seed")
    source_url: Mapped[str] = mapped_column(String(512), default="")
    source_quote: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    venue: Mapped[Venue] = relationship(back_populates="verifications")


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    query_text: Mapped[str] = mapped_column(Text, default="")
    query_text_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    parsed_intent_json: Mapped[str] = mapped_column(Text, default="")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    engine: Mapped[str] = mapped_column(String(32), default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RefreshRun(Base):
    __tablename__ = "refresh_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="all")
    status: Mapped[str] = mapped_column(String(32), default="running")
    diff_summary_json: Mapped[str] = mapped_column(Text, default="{}")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tokens: Mapped[list[AuthToken]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="tokens")


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ScrapedCandidate(Base):
    __tablename__ = "scraped_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    org: Mapped[str] = mapped_column(String(128), default="")
    venue_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    parser_version: Mapped[str] = mapped_column(String(32), default="v1")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    diff_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)

    __table_args__ = (Index("ix_scraped_candidates_status_source", "status", "source"),)
