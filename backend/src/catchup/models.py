"""SQLAlchemy models for catch-up.

Slice 001: member, place, roster_invite, signin_token, session.
Slice 002 adds: trip, overlap (see specs/002-map-trips-overlaps/data-model.md).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CHAR, Boolean, Date, DateTime, Float, ForeignKey, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Place(Base):
    __tablename__ = "place"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    country_name: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Member(Base):
    __tablename__ = "member"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    home_place_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("place.id"), nullable=True)
    job_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_e164: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    digest_opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    home_place: Mapped[Place | None] = relationship(lazy="joined")

    @property
    def photo_url(self) -> str | None:
        """Path to the session-gated avatar proxy (the bucket is private; browsers
        fetch this same-origin route with the auth cookie). `?v=` busts the cache
        when a re-upload changes the key."""
        if not self.photo_key:
            return None
        version = hashlib.sha256(self.photo_key.encode()).hexdigest()[:8]
        return f"/api/members/{self.id}/avatar?v={version}"


class RosterInvite(Base):
    __tablename__ = "roster_invite"

    email: Mapped[str] = mapped_column(CITEXT, primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SigninToken(Base):
    __tablename__ = "signin_token"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "session"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("member.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Trip(Base):
    """A member's planned presence at a destination over an inclusive day range."""

    __tablename__ = "trip"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), nullable=False, index=True
    )
    place_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("place.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped[Member] = relationship(lazy="joined")
    place: Mapped[Place] = relationship(lazy="joined")


class Overlap(Base):
    """A reconciled match between an unordered member pair at a shared scope.

    Written only by the overlap runner; never user-edited. `member_a_id` is always
    < `member_b_id` so each pair is stored once (data-model.md).
    """

    __tablename__ = "overlap"
    __table_args__ = (UniqueConstraint("member_a_id", "member_b_id", "kind", "scope_key", name="uq_overlap_identity"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_a_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_b_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)  # 'trip-trip' | 'trip-home'
    strength: Mapped[str] = mapped_column(Text, nullable=False)  # 'strong' | 'medium'
    place_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("place.id"), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    scope_key: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    place: Mapped[Place | None] = relationship(lazy="joined")


class SignificantEvent(Base):
    """A member's significant event at their home — an open invitation (e.g. birthday).

    Anchored to the host's `home_place` (resolved at read time); something elsewhere
    is modelled as a trip instead. Inclusive `[start_date, end_date]` day range.
    """

    __tablename__ = "significant_event"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("member.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped[Member] = relationship(lazy="joined")

    @property
    def place(self) -> Place | None:
        """The host's home location (events are anchored to home), resolved at read time."""
        return self.member.home_place
