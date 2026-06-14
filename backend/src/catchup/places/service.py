"""Shared place dedup: single source of `upsert_place`, used by members + trips."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import PlaceSchema
from catchup.models import Place


def upsert_place(db: DbSession, place: PlaceSchema) -> Place:
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
