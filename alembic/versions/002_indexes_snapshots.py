"""indexes, snapshots, query log hash

Revision ID: 002
Revises: 001
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_venues_source_active_arr", "venues", ["source", "active", "arrondissement"])
    op.create_index("ix_refresh_runs_started_at", "refresh_runs", ["started_at"])
    op.add_column("query_log", sa.Column("query_text_hash", sa.String(length=64), server_default=""))
    op.create_index("ix_query_log_query_text_hash", "query_log", ["query_text_hash"])
    op.create_table(
        "data_snapshots",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("payload", sa.Text(), server_default=""),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("data_snapshots")
    op.drop_index("ix_query_log_query_text_hash", table_name="query_log")
    op.drop_column("query_log", "query_text_hash")
    op.drop_index("ix_refresh_runs_started_at", table_name="refresh_runs")
    op.drop_index("ix_venues_source_active_arr", table_name="venues")
