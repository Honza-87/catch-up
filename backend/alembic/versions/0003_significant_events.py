"""significant events: significant_event table

Revision ID: 0003_significant_events
Revises: 0002_trips_overlaps
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision: str = "0003_significant_events"
down_revision: str | None = "0002_trips_overlaps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "significant_event",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_significant_event_member_id", "significant_event", ["member_id"])


def downgrade() -> None:
    op.drop_index("ix_significant_event_member_id", table_name="significant_event")
    op.drop_table("significant_event")
