"""Overlap runner: load presences, detect, and reconcile the `overlap` table.

The I/O edge around the pure engine (Constitution IV). Idempotent: each pass
inserts newly-detected overlaps (notified_at NULL), deletes vanished ones, and
updates dates on still-matching rows while preserving `notified_at` (a date shift
is not a new alert — data-model.md / research §3).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from catchup.models import Member, Overlap, Trip
from catchup.notify.base import Notifier, OverlapDigestItem
from catchup.overlaps.detection import DetectedOverlap, Presence, detect_overlaps

logger = logging.getLogger(__name__)


def _scope_key(o: DetectedOverlap) -> str:
    return str(o.place_id) if o.strength == "strong" else o.country_code


def _load_presences(db: DbSession, today: date) -> list[Presence]:
    presences: list[Presence] = []

    members = db.execute(select(Member).where(Member.home_place_id.isnot(None))).scalars().all()
    for m in members:
        hp = m.home_place
        assert hp is not None  # guarded by the WHERE clause
        presences.append(Presence(m.id, hp.id, hp.country_code, hp.lat, hp.lng, "home", None, None))

    trips = db.execute(select(Trip).where(Trip.end_date >= today)).scalars().all()
    for t in trips:
        p = t.place
        presences.append(
            Presence(t.member_id, t.place_id, p.country_code, p.lat, p.lng, "trip", t.start_date, t.end_date)
        )

    return presences


def reconcile(db: DbSession, today: date | None = None) -> int:
    """Bring the `overlap` table in line with freshly detected overlaps.

    Returns the number of newly inserted overlaps.
    """
    today = today or datetime.now(UTC).date()
    desired = detect_overlaps(_load_presences(db, today), today)
    desired_by_key = {(d.member_a, d.member_b, d.kind, _scope_key(d)): d for d in desired}

    existing = db.execute(select(Overlap)).scalars().all()
    existing_by_key = {(o.member_a_id, o.member_b_id, o.kind, o.scope_key): o for o in existing}

    for key, row in existing_by_key.items():
        if key not in desired_by_key:
            db.delete(row)

    inserted = 0
    for key, d in desired_by_key.items():
        row = existing_by_key.get(key)
        if row is None:
            db.add(
                Overlap(
                    member_a_id=d.member_a,
                    member_b_id=d.member_b,
                    kind=d.kind,
                    strength=d.strength,
                    place_id=d.place_id,
                    country_code=d.country_code,
                    scope_key=_scope_key(d),
                    start_date=d.start_date,
                    end_date=d.end_date,
                    notified_at=None,
                )
            )
            inserted += 1
        else:
            # Still detected: refresh dates only, keep notified_at (no re-alert on shift).
            row.start_date = d.start_date
            row.end_date = d.end_date

    db.flush()
    logger.info("Overlap reconcile: %d desired, %d inserted", len(desired_by_key), inserted)
    return inserted


def _digest_item(o: Overlap, recipient_id: UUID, members: dict[UUID, Member]) -> OverlapDigestItem:
    other_id = o.member_b_id if o.member_a_id == recipient_id else o.member_a_id
    other = members[other_id]
    return OverlapDigestItem(
        other_member_name=other.display_name,
        place_label=o.place.city if o.place is not None else None,
        country_name=o.place.country_name if o.place is not None else o.country_code,
        strength=o.strength,
        start_date=o.start_date,
        end_date=o.end_date,
    )


def notify_new(db: DbSession, notifier: Notifier) -> int:
    """Send one digest per affected member for not-yet-notified overlaps.

    Stamps `notified_at` on an overlap only after *both* its members' digests have
    been sent successfully; a send failure leaves rows un-notified for the next run
    (FR-022/FR-024 / research §3). Returns the number of digests sent.
    """
    pending = list(db.execute(select(Overlap).where(Overlap.notified_at.is_(None))).scalars().all())
    if not pending:
        return 0

    member_ids = {o.member_a_id for o in pending} | {o.member_b_id for o in pending}
    members = {m.id: m for m in db.execute(select(Member).where(Member.id.in_(member_ids))).scalars().all()}

    by_member: dict[UUID, list[Overlap]] = {}
    for o in pending:
        by_member.setdefault(o.member_a_id, []).append(o)
        by_member.setdefault(o.member_b_id, []).append(o)

    sent_for: dict[UUID, set[UUID]] = {o.id: set() for o in pending}
    digests = 0
    for member_id, overlaps in by_member.items():
        member = members[member_id]
        items = [_digest_item(o, member_id, members) for o in overlaps]
        try:
            notifier.send_overlap_digest(member.email, member.display_name, items)
        except Exception:
            logger.warning("Overlap digest failed for %s; will retry next run", member.email, exc_info=True)
            continue
        digests += 1
        for o in overlaps:
            sent_for[o.id].add(member_id)

    now = datetime.now(UTC)
    for o in pending:
        if {o.member_a_id, o.member_b_id} <= sent_for[o.id]:
            o.notified_at = now

    db.flush()
    logger.info("Overlap notify: %d digests sent", digests)
    return digests
