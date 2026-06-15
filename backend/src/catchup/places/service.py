"""Shared place dedup: single source of `upsert_place`, used by members + trips."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import PlaceSchema
from catchup.models import Place


def upsert_place(db: DbSession, place: PlaceSchema) -> Place:
    """Reuse an existing nearby place with the same city/country, else create one.

    Geocoded places match on same city + country within a ~55 km (0.5°) box. The
    box only disambiguates genuine homonyms (same city name + country far apart,
    e.g. Springfield); it's deliberately loose so the *same* city geocoded slightly
    differently (centre vs a suburb point, or two geocoder results) still collapses
    to one place — otherwise two people heading to the same destination would grade
    as a weak "medium" (same country) instead of "strong" (same city). Manual
    entries (geocoder down → FR-007) arrive with sentinel 0,0 coordinates; they
    match on city + country alone so they snap onto a real geocoded row when one
    exists (correct overlaps + a placeable map pin).
    """
    query = select(Place).where(Place.city == place.city, Place.country_code == place.country_code)
    if place.lat != 0 or place.lng != 0:
        query = query.where(
            func.abs(Place.lat - place.lat) < 0.5,
            func.abs(Place.lng - place.lng) < 0.5,
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
