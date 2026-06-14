"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class PlaceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    country_code: str
    country_name: str
    lat: float
    lng: float


class MemberSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None
    photo_url: str | None
    home_place: PlaceSchema | None
    job_title: str | None
    company: str | None
    whatsapp_e164: str | None


class MemberDetail(MemberSummary):
    email: str
    note: str | None
    created_at: datetime


class RequestLinkBody(BaseModel):
    email: EmailStr


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    job_title: str | None = None
    company: str | None = None
    note: str | None = None
    whatsapp_e164: str | None = None
    home_place: PlaceSchema | None = None
