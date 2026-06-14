"""Pure mapping from geocoder (Photon) features to Place dicts (no I/O)."""

from __future__ import annotations

from typing import Any


def feature_to_place(feature: dict[str, Any]) -> dict[str, Any] | None:
    """Map a single Photon GeoJSON feature to a place dict, or None if incomplete."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates")
    city = props.get("city") or props.get("name")
    country = props.get("country")
    country_code = props.get("countrycode")
    if not (city and country and country_code and coords and len(coords) == 2):
        return None
    lng, lat = coords[0], coords[1]
    return {
        "city": city,
        "country_code": str(country_code).upper(),
        "country_name": country,
        "lat": float(lat),
        "lng": float(lng),
    }


def features_to_places(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map and de-duplicate a list of Photon features to place dicts."""
    seen: set[tuple] = set()
    out: list[dict[str, Any]] = []
    for feature in features:
        place = feature_to_place(feature)
        if place is None:
            continue
        key = (place["city"], place["country_code"], round(place["lat"], 3), round(place["lng"], 3))
        if key in seen:
            continue
        seen.add(key)
        out.append(place)
    return out
