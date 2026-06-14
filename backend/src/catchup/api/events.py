"""Significant-event routes: own-event CRUD + class-wide upcoming list (invitations)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import EventCreate, EventSchema, EventUpdate
from catchup.auth.deps import get_current_member
from catchup.db import get_session
from catchup.events import service
from catchup.models import Member

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(_: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    """All upcoming events across the class (the invitations surface)."""
    events = service.list_all_upcoming(db, datetime.now(UTC).date())
    return {"events": [EventSchema.model_validate(e) for e in events]}


@router.get("/me")
def list_my_events(member: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    return {"events": [EventSchema.model_validate(e) for e in service.list_own_events(db, member)]}


@router.post("", status_code=201)
def create_event(
    body: EventCreate,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    return {"event": EventSchema.model_validate(service.create_event(db, member, body))}


@router.patch("/{event_id}")
def update_event(
    event_id: UUID,
    body: EventUpdate,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    return {"event": EventSchema.model_validate(service.update_event(db, member, event_id, body))}


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: UUID,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> None:
    service.delete_event(db, member, event_id)
