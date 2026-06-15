"""member digest opt-out: member.digest_opt_out flag

Revision ID: 0004_member_digest_opt_out
Revises: 0003_significant_events
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_member_digest_opt_out"
down_revision: str | None = "0003_significant_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member",
        sa.Column("digest_opt_out", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("member", "digest_opt_out")
