"""Unit tests for the pure overlap engine (no DB, no I/O)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from catchup.overlaps.detection import Presence, detect_overlaps

# Stable, readable ids.
LISBON = UUID(int=10)
PORTO = UUID(int=11)
BERLIN = UUID(int=12)
TOKYO = UUID(int=13)

EARLY = date(2026, 1, 1)  # "today" earlier than every fixture date → no clamping


def mid(n: int) -> UUID:
    return UUID(int=100 + n)


def trip(member: int, place: UUID, cc: str, start: tuple[int, int, int], end: tuple[int, int, int]) -> Presence:
    return Presence(mid(member), place, cc, 0.0, 0.0, "trip", date(*start), date(*end))


def home(member: int, place: UUID, cc: str) -> Presence:
    return Presence(mid(member), place, cc, 0.0, 0.0, "home", None, None)


def test_trip_trip_same_city_is_strong():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(2, LISBON, "PT", (2026, 7, 5), (2026, 7, 15))], EARLY
    )
    assert len(out) == 1
    o = out[0]
    assert o.strength == "strong"
    assert o.kind == "trip-trip"
    assert o.place_id == LISBON
    assert o.country_code == "PT"
    assert (o.start_date, o.end_date) == (date(2026, 7, 5), date(2026, 7, 10))
    assert o.member_a < o.member_b


def test_trip_trip_same_country_diff_city_is_medium():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(2, PORTO, "PT", (2026, 7, 5), (2026, 7, 15))], EARLY
    )
    assert len(out) == 1
    assert out[0].strength == "medium"
    assert out[0].place_id is None
    assert out[0].country_code == "PT"


def test_different_country_no_overlap():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(2, TOKYO, "JP", (2026, 7, 5), (2026, 7, 15))], EARLY
    )
    assert out == []


def test_disjoint_dates_no_overlap():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 5)), trip(2, LISBON, "PT", (2026, 7, 10), (2026, 7, 15))], EARLY
    )
    assert out == []


def test_trip_home_same_city_strong():
    out = detect_overlaps([trip(1, BERLIN, "DE", (2026, 7, 1), (2026, 7, 10)), home(2, BERLIN, "DE")], EARLY)
    assert len(out) == 1
    assert out[0].kind == "trip-home"
    assert out[0].strength == "strong"
    assert out[0].place_id == BERLIN
    assert (out[0].start_date, out[0].end_date) == (date(2026, 7, 1), date(2026, 7, 10))


def test_trip_home_same_country_medium():
    out = detect_overlaps([trip(1, PORTO, "PT", (2026, 7, 1), (2026, 7, 10)), home(2, LISBON, "PT")], EARLY)
    assert len(out) == 1
    assert out[0].kind == "trip-home"
    assert out[0].strength == "medium"
    assert out[0].place_id is None


def test_resident_away_whole_window_suppresses_trip_home():
    presences = [
        trip(1, BERLIN, "DE", (2026, 7, 1), (2026, 7, 10)),
        home(2, BERLIN, "DE"),
        trip(2, TOKYO, "JP", (2026, 6, 20), (2026, 7, 20)),  # resident away the entire visit
    ]
    assert detect_overlaps(presences, EARLY) == []


def test_resident_away_partial_trims_window():
    presences = [
        trip(1, BERLIN, "DE", (2026, 7, 1), (2026, 7, 10)),
        home(2, BERLIN, "DE"),
        trip(2, TOKYO, "JP", (2026, 7, 5), (2026, 7, 20)),  # away from the 5th on
    ]
    out = detect_overlaps(presences, EARLY)
    assert len(out) == 1
    assert out[0].kind == "trip-home"
    assert (out[0].start_date, out[0].end_date) == (date(2026, 7, 1), date(2026, 7, 4))


def test_home_home_excluded():
    assert detect_overlaps([home(1, LISBON, "PT"), home(2, LISBON, "PT")], EARLY) == []


def test_self_excluded():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(1, LISBON, "PT", (2026, 7, 5), (2026, 7, 15))], EARLY
    )
    assert out == []


def test_pair_canonicalized_regardless_of_input_order():
    a = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(2, LISBON, "PT", (2026, 7, 1), (2026, 7, 10))], EARLY
    )
    b = detect_overlaps(
        [trip(2, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10))], EARLY
    )
    assert a[0].member_a == b[0].member_a == mid(1)
    assert a[0].member_b == b[0].member_b == mid(2)


def test_strongest_first_ordering():
    presences = [
        # strong pair (1,2) Lisbon
        trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)),
        trip(2, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)),
        # medium pair (3,4) Lisbon/Porto same country
        trip(3, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)),
        trip(4, PORTO, "PT", (2026, 7, 1), (2026, 7, 10)),
    ]
    out = detect_overlaps(presences, EARLY)
    strengths = [o.strength for o in out]
    assert strengths == sorted(strengths, key=lambda s: 0 if s == "strong" else 1)
    assert out[0].strength == "strong"


def test_past_overlap_dropped_by_today():
    out = detect_overlaps(
        [trip(1, LISBON, "PT", (2026, 7, 1), (2026, 7, 10)), trip(2, LISBON, "PT", (2026, 7, 1), (2026, 7, 10))],
        date(2026, 8, 1),  # today after the trips
    )
    assert out == []
