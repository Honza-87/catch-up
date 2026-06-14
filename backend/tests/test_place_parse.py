"""Unit tests for pure geocoder-feature → Place mapping (no I/O)."""

from __future__ import annotations

from catchup.places.parse import feature_to_place, features_to_places


def _feature(name="Lisbon", country="Portugal", cc="pt", lng=-9.139, lat=38.722):
    return {
        "geometry": {"coordinates": [lng, lat]},
        "properties": {"name": name, "country": country, "countrycode": cc},
    }


def test_feature_to_place_maps_fields():
    place = feature_to_place(_feature())
    assert place == {
        "city": "Lisbon",
        "country_code": "PT",
        "country_name": "Portugal",
        "lat": 38.722,
        "lng": -9.139,
    }


def test_feature_to_place_none_when_incomplete():
    assert feature_to_place({"properties": {"name": "X"}}) is None
    assert feature_to_place({"geometry": {"coordinates": [1, 2]}, "properties": {}}) is None


def test_features_to_places_dedupes():
    features = [_feature(), _feature(), _feature(name="Porto", cc="pt", lng=-8.61, lat=41.15)]
    places = features_to_places(features)
    assert len(places) == 2
    assert {p["city"] for p in places} == {"Lisbon", "Porto"}
