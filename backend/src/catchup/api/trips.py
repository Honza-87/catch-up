"""Trip routes: own-trip CRUD + class-wide upcoming list. All session-gated."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import TripCreate, TripSchema, TripUpdate
from catchup.auth.deps import get_current_member
from catchup.db import get_session
from catchup.models import Member
from catchup.trips import service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("")
def list_trips(_: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    """All upcoming trips across the class (map + panel)."""
    trips = service.list_all_upcoming(db, datetime.now(UTC).date())
    return {"trips": [TripSchema.model_validate(t) for t in trips]}


@router.get("/me")
def list_my_trips(member: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    trips = service.list_own_trips(db, member)
    return {"trips": [TripSchema.model_validate(t) for t in trips]}


@router.post("", status_code=201)
def create_trip(
    body: TripCreate,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    trip = service.create_trip(db, member, body)
    return {"trip": TripSchema.model_validate(trip)}


@router.patch("/{trip_id}")
def update_trip(
    trip_id: UUID,
    body: TripUpdate,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    trip = service.update_trip(db, member, trip_id, body)
    return {"trip": TripSchema.model_validate(trip)}


@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: UUID,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> None:
    service.delete_trip(db, member, trip_id)
