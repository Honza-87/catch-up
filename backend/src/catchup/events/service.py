"""Significant-event service: self-service CRUD, anchored to the host's home."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import EventCreate, EventUpdate
from catchup.errors import AppError
from catchup.events.validation import validate_event_dates
from catchup.models import Member, SignificantEvent


def list_own_events(db: DbSession, member: Member) -> list[SignificantEvent]:
    return list(
        db.execute(
            select(SignificantEvent)
            .where(SignificantEvent.member_id == member.id)
            .order_by(SignificantEvent.start_date)
        )
        .scalars()
        .all()
    )


def list_all_upcoming(db: DbSession, today: date) -> list[SignificantEvent]:
    return list(
        db.execute(
            select(SignificantEvent).where(SignificantEvent.end_date >= today).order_by(SignificantEvent.start_date)
        )
        .scalars()
        .all()
    )


def create_event(db: DbSession, member: Member, data: EventCreate) -> SignificantEvent:
    if member.home_place_id is None:
        raise AppError("no_home", "Set your home location before adding an event.", status_code=422)
    validate_event_dates(data.start_date, data.end_date)
    event = SignificantEvent(
        member_id=member.id,
        title=data.title,
        start_date=data.start_date,
        end_date=data.end_date,
        note=data.note,
    )
    db.add(event)
    db.flush()
    return event


def _own_event_or_raise(db: DbSession, member: Member, event_id: UUID) -> SignificantEvent:
    event = db.get(SignificantEvent, event_id)
    if event is None:
        raise AppError("not_found", "No such event.", status_code=404)
    if event.member_id != member.id:
        raise AppError("forbidden", "Not your event.", status_code=403)
    return event


def update_event(db: DbSession, member: Member, event_id: UUID, data: EventUpdate) -> SignificantEvent:
    event = _own_event_or_raise(db, member, event_id)
    sent = data.model_fields_set

    start = data.start_date if "start_date" in sent else event.start_date
    end = data.end_date if "end_date" in sent else event.end_date
    validate_event_dates(start, end)
    event.start_date = start
    event.end_date = end

    if "title" in sent and data.title is not None:
        event.title = data.title
    if "note" in sent:
        event.note = data.note

    db.flush()
    return event


def delete_event(db: DbSession, member: Member, event_id: UUID) -> None:
    event = _own_event_or_raise(db, member, event_id)
    db.delete(event)
    db.flush()
