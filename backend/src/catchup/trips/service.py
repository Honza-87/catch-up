"""Trip service: self-service CRUD with server-side ownership enforcement."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import TripCreate, TripUpdate
from catchup.errors import AppError
from catchup.models import Member, Trip
from catchup.places.service import upsert_place
from catchup.trips.validation import validate_trip_dates


def list_own_trips(db: DbSession, member: Member) -> list[Trip]:
    """The caller's own trips, soonest first (includes past for self-management)."""
    return list(db.execute(select(Trip).where(Trip.member_id == member.id).order_by(Trip.start_date)).scalars().all())


def list_all_upcoming(db: DbSession, today: date) -> list[Trip]:
    """Every member's upcoming trips (end_date >= today), soonest first (FR for map)."""
    return list(db.execute(select(Trip).where(Trip.end_date >= today).order_by(Trip.start_date)).scalars().all())


def create_trip(db: DbSession, member: Member, data: TripCreate) -> Trip:
    validate_trip_dates(data.start_date, data.end_date)
    place = upsert_place(db, data.place)
    trip = Trip(
        member_id=member.id,
        place_id=place.id,
        start_date=data.start_date,
        end_date=data.end_date,
        note=data.note,
    )
    db.add(trip)
    db.flush()
    return trip


def _own_trip_or_raise(db: DbSession, member: Member, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise AppError("not_found", "No such trip.", status_code=404)
    if trip.member_id != member.id:
        raise AppError("forbidden", "Not your trip.", status_code=403)
    return trip


def update_trip(db: DbSession, member: Member, trip_id: UUID, data: TripUpdate) -> Trip:
    trip = _own_trip_or_raise(db, member, trip_id)
    sent = data.model_fields_set

    start = data.start_date if "start_date" in sent else trip.start_date
    end = data.end_date if "end_date" in sent else trip.end_date
    validate_trip_dates(start, end)
    trip.start_date = start
    trip.end_date = end

    if "place" in sent and data.place is not None:
        trip.place = upsert_place(db, data.place)
    if "note" in sent:
        trip.note = data.note

    db.flush()
    return trip


def delete_trip(db: DbSession, member: Member, trip_id: UUID) -> None:
    trip = _own_trip_or_raise(db, member, trip_id)
    db.delete(trip)
    db.flush()
