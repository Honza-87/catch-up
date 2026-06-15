"""member photo as private-bucket key: rename member.photo_url -> photo_key

Photos are served through an authed proxy route, not a public URL, so the
column now holds the S3 object key rather than a public URL.

Revision ID: 0005_member_photo_key
Revises: 0004_member_digest_opt_out
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_member_photo_key"
down_revision: str | None = "0004_member_digest_opt_out"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("member", "photo_url", new_column_name="photo_key")


def downgrade() -> None:
    op.alter_column("member", "photo_key", new_column_name="photo_url")
