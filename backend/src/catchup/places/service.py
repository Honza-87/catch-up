"""Shared place dedup: single source of `upsert_place`, used by members + trips."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import PlaceSchema
from catchup.models import Place


def upsert_place(db: DbSession, place: PlaceSchema) -> Place:
    """Reuse an existing nearby place with the same city/country, else create one.

    Geocoded places match on near-coordinates (dedup distinct cities that share a
    name). Manual entries (geocoder down → FR-007) arrive with sentinel 0,0
    coordinates; they match on city + country alone so they snap onto a real
    geocoded row when one exists (correct overlaps + a placeable map pin).
    """
    query = select(Place).where(Place.city == place.city, Place.country_code == place.country_code)
    if place.lat != 0 or place.lng != 0:
        query = query.where(
            func.abs(Place.lat - place.lat) < 0.01,
            func.abs(Place.lng - place.lng) < 0.01,
        )
    existing = db.execute(query).scalars().first()
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
