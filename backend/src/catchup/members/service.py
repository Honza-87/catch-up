"""Member profile service: own-profile updates, home-place upsert, directory."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import PlaceSchema, ProfileUpdate
from catchup.config import Settings
from catchup.errors import AppError
from catchup.members.validation import normalize_whatsapp
from catchup.models import Member, Place

_PLAIN_FIELDS = ("display_name", "job_title", "company", "note")


def get_member(db: DbSession, member_id: UUID) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise AppError("not_found", "No such member.", status_code=404)
    return member


def list_directory(db: DbSession) -> list[Member]:
    """All joined members (FR-016: a member row exists only after first sign-in)."""
    return list(db.execute(select(Member).order_by(Member.display_name, Member.email)).scalars().all())


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
        member.home_place = None if data.home_place is None else _upsert_place(db, data.home_place)

    db.flush()
    return member


def set_photo(db: DbSession, member: Member, url: str) -> None:
    member.photo_url = url
    db.flush()


def clear_photo(db: DbSession, member: Member) -> None:
    member.photo_url = None
    db.flush()


def _upsert_place(db: DbSession, place: PlaceSchema) -> Place:
    """Reuse an existing nearby place with the same city/country, else create one."""
    existing = (
        db.execute(
            select(Place).where(
                Place.city == place.city,
                Place.country_code == place.country_code,
                func.abs(Place.lat - place.lat) < 0.01,
                func.abs(Place.lng - place.lng) < 0.01,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return existing
    row = Place(
        city=place.city,
        country_code=place.country_code,
        country_name=place.country_name,
        lat=place.lat,
        lng=place.lng,
    )
    db.add(row)
    db.flush()
    return row
