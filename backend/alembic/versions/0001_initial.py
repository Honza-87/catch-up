"""initial schema: member, place, roster_invite, signin_token, session

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "place",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("country_code", sa.CHAR(2), nullable=False),
        sa.Column("country_name", sa.Text(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "member",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("email", CITEXT(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("home_place_id", PgUUID(as_uuid=True), sa.ForeignKey("place.id"), nullable=True),
        sa.Column("job_title", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("whatsapp_e164", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_member_email", "member", ["email"], unique=True)

    op.create_table(
        "roster_invite",
        sa.Column("email", CITEXT(), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_table(
        "signin_token",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("email", CITEXT(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signin_token_email", "signin_token", ["email"])
    op.create_index("ix_signin_token_token_hash", "signin_token", ["token_hash"], unique=True)
    op.create_index("ix_signin_token_expires_at", "signin_token", ["expires_at"])

    op.create_table(
        "session",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("member_id", PgUUID(as_uuid=True), sa.ForeignKey("member.id"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_session_token_hash", "session", ["token_hash"], unique=True)
    op.create_index("ix_session_member_id", "session", ["member_id"])


def downgrade() -> None:
    op.drop_table("session")
    op.drop_table("signin_token")
    op.drop_table("roster_invite")
    op.drop_index("ix_member_email", table_name="member")
    op.drop_table("member")
    op.drop_table("place")
