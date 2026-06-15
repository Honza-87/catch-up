"""Member profile service: own-profile updates, home-place upsert, directory."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import ProfileUpdate
from catchup.config import Settings
from catchup.errors import AppError
from catchup.members.validation import normalize_whatsapp
from catchup.models import Member, SignificantEvent, Trip
from catchup.places.service import upsert_place

_PLAIN_FIELDS = ("display_name", "job_title", "company", "note", "digest_opt_out")


def get_member(db: DbSession, member_id: UUID) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise AppError("not_found", "No such member.", status_code=404)
    # Attach upcoming trips + events (sorted) so MemberDetail renders the drawer in one call.
    today = datetime.now(UTC).date()
    member.trips = list(
        db.execute(select(Trip).where(Trip.member_id == member_id, Trip.end_date >= today).order_by(Trip.start_date))
        .scalars()
        .all()
    )
    member.events = list(
        db.execute(
            select(SignificantEvent)
            .where(SignificantEvent.member_id == member_id, SignificantEvent.end_date >= today)
            .order_by(SignificantEvent.start_date)
        )
        .scalars()
        .all()
    )
    return member


def list_directory(db: DbSession) -> list[Member]:
    """Joined members who have started their profile (have a display name).

    A row exists after first sign-in (FR-016), but someone who signed in without
    filling anything would otherwise show as a blank card, so hide name-less rows.
    """
    return list(
        db.execute(select(Member).where(Member.display_name.isnot(None)).order_by(Member.display_name, Member.email))
        .scalars()
        .all()
    )


def update_own_profile(db: DbSession, member: Member, data: ProfileUpdate, settings: Settings) -> Member:
    """Apply only the fields the caller actually sent; member edits self only."""
    sent = data.model_fields_set

    for field in _PLAIN_FIELDS:
        if field in sent:
            setattr(member, field, getattr(data, field))

    if "whatsapp_e164" in sent:
        raw = data.whatsapp_e164
        member.whatsapp_e164 = normalize_whatsapp(raw) if raw else None

    if "home_place" in sent:
        member.home_place = None if data.home_place is None else upsert_place(db, data.home_place)

    db.flush()
    return member


def set_photo(db: DbSession, member: Member, key: str) -> None:
    member.photo_key = key
    db.flush()


def clear_photo(db: DbSession, member: Member) -> None:
    member.photo_key = None
    db.flush()
