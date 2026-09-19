"""scraped_candidates staging table

Revision ID: 003
Revises: 002
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scraped_candidates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("org", sa.String(length=128), server_default=""),
        sa.Column("venue_id", sa.String(length=64), nullable=True),
        sa.Column("parser_version", sa.String(length=32), server_default="v1"),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), server_default="{}"),
        sa.Column("diff_json", sa.Text(), server_default="{}"),
        sa.Column("status", sa.String(length=16), server_default="new"),
    )
    op.create_index("ix_scraped_candidates_source", "scraped_candidates", ["source"])
    op.create_index("ix_scraped_candidates_venue_id", "scraped_candidates", ["venue_id"])
    op.create_index("ix_scraped_candidates_content_hash", "scraped_candidates", ["content_hash"])
    op.create_index("ix_scraped_candidates_status", "scraped_candidates", ["status"])
    op.create_index("ix_scraped_candidates_status_source", "scraped_candidates", ["status", "source"])


def downgrade() -> None:
    op.drop_index("ix_scraped_candidates_status_source", table_name="scraped_candidates")
    op.drop_index("ix_scraped_candidates_status", table_name="scraped_candidates")
    op.drop_index("ix_scraped_candidates_content_hash", table_name="scraped_candidates")
    op.drop_index("ix_scraped_candidates_venue_id", table_name="scraped_candidates")
    op.drop_index("ix_scraped_candidates_source", table_name="scraped_candidates")
    op.drop_table("scraped_candidates")
