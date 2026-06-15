"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class PlaceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    country_code: str
    country_name: str
    lat: float
    lng: float


class MemberLite(BaseModel):
    """Minimal member identity embedded in trip/overlap responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None
    photo_url: str | None


class MemberSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None
    photo_url: str | None
    home_place: PlaceSchema | None
    job_title: str | None
    company: str | None
    whatsapp_e164: str | None


class TripSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member: MemberLite
    place: PlaceSchema
    start_date: date
    end_date: date
    note: str | None


class TripCreate(BaseModel):
    place: PlaceSchema
    start_date: date
    end_date: date
    note: str | None = None


class TripUpdate(BaseModel):
    place: PlaceSchema | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None


class OverlapSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    other_member: MemberLite
    kind: str
    strength: str
    place: PlaceSchema | None
    country_code: str
    start_date: date
    end_date: date


class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member: MemberLite
    place: PlaceSchema | None  # the host's home location at read time
    title: str
    start_date: date
    end_date: date
    note: str | None


class EventCreate(BaseModel):
    title: str
    start_date: date
    end_date: date
    note: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None


class MemberDetail(MemberSummary):
    email: str
    note: str | None
    digest_opt_out: bool
    created_at: datetime
    trips: list[TripSchema] = []
    events: list[EventSchema] = []


class RequestLinkBody(BaseModel):
    email: EmailStr


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    job_title: str | None = None
    company: str | None = None
    note: str | None = None
    whatsapp_e164: str | None = None
    home_place: PlaceSchema | None = None
    digest_opt_out: bool | None = None
