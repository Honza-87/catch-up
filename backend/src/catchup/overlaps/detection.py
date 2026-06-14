"""Pure overlap engine: presences → graded overlaps. No DB, no I/O.

The heart of the product (Constitution IV). Models each member's whereabouts as
presence intervals (trips, plus an always-present home minus the member's own
trips) and detects pairwise interval intersections, grading them strong (same
city) or medium (same country, different city) across trip↔trip and trip↔home.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

_MIN = date.min
_MAX = date.max


@dataclass(frozen=True)
class Presence:
    """A member's presence at a place over an interval.

    `source` is "trip" or "home". Home presences use open bounds (`start`/`end`
    = None), meaning always-present; the engine subtracts the member's own trips.
    """

    member_id: UUID
    place_id: UUID
    country_code: str
    lat: float
    lng: float
    source: str
    start: date | None
    end: date | None


@dataclass(frozen=True)
class DetectedOverlap:
    """The canonical, unordered result the runner persists."""

    member_a: UUID
    member_b: UUID
    kind: str  # "trip-trip" | "trip-home"
    strength: str  # "strong" | "medium"
    place_id: UUID | None
    country_code: str
    start_date: date
    end_date: date


def _intersect(a_start: date, a_end: date, b_start: date, b_end: date) -> tuple[date, date] | None:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return (start, end) if start <= end else None


def _subtract(start: date, end: date, aways: list[tuple[date, date]]) -> list[tuple[date, date]]:
    """Remove inclusive `aways` day-ranges from [start, end], returning the gaps."""
    segments = [(start.toordinal(), end.toordinal())]
    for a_start, a_end in aways:
        a0, a1 = a_start.toordinal(), a_end.toordinal()
        nxt: list[tuple[int, int]] = []
        for s0, s1 in segments:
            if a1 < s0 or a0 > s1:  # disjoint
                nxt.append((s0, s1))
                continue
            if s0 < a0:
                nxt.append((s0, a0 - 1))
            if a1 < s1:
                nxt.append((a1 + 1, s1))
        segments = nxt
    return [(date.fromordinal(s0), date.fromordinal(s1)) for s0, s1 in segments if s0 <= s1]


def _grade(p: Presence, q: Presence) -> tuple[str, UUID | None] | None:
    """Return (strength, place_id) for a matching pair, or None if not even same country."""
    if p.place_id == q.place_id:
        return ("strong", p.place_id)
    if p.country_code == q.country_code:
        return ("medium", None)
    return None


def _windows(
    p: Presence, q: Presence, today: date, trips_by_member: dict[UUID, list[tuple[date, date]]]
) -> list[tuple[date, date]]:
    """The matched sub-intervals for a pair, clamped to today and home-suppressed."""
    p_start, p_end = p.start or _MIN, p.end or _MAX
    q_start, q_end = q.start or _MIN, q.end or _MAX
    base = _intersect(p_start, p_end, q_start, q_end)
    if base is None:
        return []
    start, end = base
    start = max(start, today)
    if start > end:
        return []

    # For trip↔home, subtract the resident's own trips (home = window minus own trips).
    aways: list[tuple[date, date]] = []
    if p.source == "home":
        aways += trips_by_member.get(p.member_id, [])
    if q.source == "home":
        aways += trips_by_member.get(q.member_id, [])
    if not aways:
        return [(start, end)]
    return _subtract(start, end, aways)


def detect_overlaps(presences: list[Presence], today: date) -> list[DetectedOverlap]:
    """Detect graded overlaps between unordered member pairs.

    Steps: drop fully-past presences, pairwise-intersect (subtracting a resident's
    own trips from their home), grade strong/medium, exclude home↔home and self,
    collapse to one row per (pair, kind, scope_key) keeping the widest interval,
    and order strongest-first then by start date.
    """
    live = [p for p in presences if p.end is None or p.end >= today]
    trips_by_member: dict[UUID, list[tuple[date, date]]] = {}
    for p in live:
        if p.source == "trip" and p.start is not None and p.end is not None:
            trips_by_member.setdefault(p.member_id, []).append((p.start, p.end))

    # key: (member_a, member_b, kind, scope_key) -> mutable aggregate
    collapsed: dict[tuple[UUID, UUID, str, str], dict] = {}

    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            p, q = live[i], live[j]
            if p.member_id == q.member_id:
                continue
            if p.source == "home" and q.source == "home":
                continue
            graded = _grade(p, q)
            if graded is None:
                continue
            strength, place_id = graded
            kind = "trip-trip" if p.source == "trip" and q.source == "trip" else "trip-home"

            windows = _windows(p, q, today, trips_by_member)
            if not windows:
                continue

            member_a, member_b = sorted((p.member_id, q.member_id))
            scope_key = str(place_id) if strength == "strong" else p.country_code
            key = (member_a, member_b, kind, scope_key)

            seg_start = min(w[0] for w in windows)
            seg_end = max(w[1] for w in windows)

            agg = collapsed.get(key)
            if agg is None:
                collapsed[key] = {
                    "member_a": member_a,
                    "member_b": member_b,
                    "kind": kind,
                    "strength": strength,
                    "place_id": place_id,
                    "country_code": p.country_code,
                    "start": seg_start,
                    "end": seg_end,
                }
            else:
                agg["start"] = min(agg["start"], seg_start)
                agg["end"] = max(agg["end"], seg_end)

    results = [
        DetectedOverlap(
            member_a=a["member_a"],
            member_b=a["member_b"],
            kind=a["kind"],
            strength=a["strength"],
            place_id=a["place_id"],
            country_code=a["country_code"],
            start_date=a["start"],
            end_date=a["end"],
        )
        for a in collapsed.values()
    ]
    results.sort(key=lambda o: (0 if o.strength == "strong" else 1, o.start_date))
    return results
