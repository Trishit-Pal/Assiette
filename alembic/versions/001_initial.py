"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "venues",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("org", sa.String(length=255), server_default=""),
        sa.Column("kind", sa.String(length=64), server_default="distribution"),
        sa.Column("address", sa.String(length=512), server_default=""),
        sa.Column("arrondissement", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("price_eur", sa.Float(), server_default="0"),
        sa.Column("eligibility", sa.Text(), server_default=""),
        sa.Column("booking_required", sa.Boolean(), server_default=sa.false()),
        sa.Column("booking_url", sa.String(length=512), server_default=""),
        sa.Column("source_url", sa.String(length=512), server_default=""),
        sa.Column("french_hint", sa.Text(), server_default=""),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_venues_arrondissement", "venues", ["arrondissement"])
    op.create_index("ix_venues_source", "venues", ["source"])

    op.create_table(
        "venue_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("venue_id", sa.String(length=64), sa.ForeignKey("venues.id", ondelete="CASCADE")),
        sa.Column("weekday", sa.String(length=16), nullable=False),
        sa.Column("start_time", sa.String(length=8), nullable=False),
        sa.Column("end_time", sa.String(length=8), nullable=False),
    )
    op.create_index("ix_venue_schedules_venue_id", "venue_schedules", ["venue_id"])

    op.create_table(
        "venue_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("venue_id", sa.String(length=64), sa.ForeignKey("venues.id", ondelete="CASCADE")),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_url", sa.String(length=512), server_default=""),
        sa.Column("source_screenshot_hash", sa.String(length=64), server_default=""),
        sa.Column("raw_payload", sa.Text(), server_default=""),
        sa.Column("changed_fields", sa.Text(), server_default=""),
    )

    op.create_table(
        "verification_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("venue_id", sa.String(length=64), sa.ForeignKey("venues.id", ondelete="CASCADE")),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("verifier", sa.String(length=128), server_default="seed"),
        sa.Column("source_url", sa.String(length=512), server_default=""),
        sa.Column("source_quote", sa.Text(), server_default=""),
        sa.Column("notes", sa.Text(), server_default=""),
    )

    op.create_table(
        "query_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("query_text", sa.Text(), server_default=""),
        sa.Column("parsed_intent_json", sa.Text(), server_default=""),
        sa.Column("result_count", sa.Integer(), server_default="0"),
        sa.Column("engine", sa.String(length=32), server_default=""),
        sa.Column("latency_ms", sa.Integer(), server_default="0"),
        sa.Column("user_email", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "refresh_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=64), server_default="all"),
        sa.Column("status", sa.String(length=32), server_default="running"),
        sa.Column("diff_summary_json", sa.Text(), server_default="{}"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("role", sa.String(length=32), server_default="student"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token_hash", sa.String(length=128), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("auth_tokens")
    op.drop_table("users")
    op.drop_table("refresh_runs")
    op.drop_table("query_log")
    op.drop_table("verification_log")
    op.drop_table("venue_versions")
    op.drop_table("venue_schedules")
    op.drop_index("ix_venues_source", table_name="venues")
    op.drop_index("ix_venues_arrondissement", table_name="venues")
    op.drop_table("venues")
