"""trips + overlaps: trip, overlap tables

Revision ID: 0002_trips_overlaps
Revises: 0001_initial
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision: str = "0002_trips_overlaps"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("place_id", PgUUID(as_uuid=True), sa.ForeignKey("place.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_trip_member_id", "trip", ["member_id"])

    op.create_table(
        "overlap",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_a_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "member_b_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("strength", sa.Text(), nullable=False),
        sa.Column("place_id", PgUUID(as_uuid=True), sa.ForeignKey("place.id"), nullable=True),
        sa.Column("country_code", sa.CHAR(2), nullable=False),
        sa.Column("scope_key", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("member_a_id", "member_b_id", "kind", "scope_key", name="uq_overlap_identity"),
    )
    op.create_index("ix_overlap_member_a_id", "overlap", ["member_a_id"])
    op.create_index("ix_overlap_member_b_id", "overlap", ["member_b_id"])


def downgrade() -> None:
    op.drop_index("ix_overlap_member_b_id", table_name="overlap")
    op.drop_index("ix_overlap_member_a_id", table_name="overlap")
    op.drop_table("overlap")
    op.drop_index("ix_trip_member_id", table_name="trip")
    op.drop_table("trip")
