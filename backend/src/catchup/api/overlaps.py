"""Overlap routes: the caller's own overlaps, strongest-first. Read-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import MemberLite, OverlapSchema, PlaceSchema
from catchup.auth.deps import get_current_member
from catchup.db import get_session
from catchup.models import Member, Overlap

router = APIRouter(prefix="/overlaps", tags=["overlaps"])


@router.get("/me")
def my_overlaps(member: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    rows = list(
        db.execute(select(Overlap).where(or_(Overlap.member_a_id == member.id, Overlap.member_b_id == member.id)))
        .scalars()
        .all()
    )
    rows.sort(key=lambda o: (0 if o.strength == "strong" else 1, o.start_date))

    overlaps = []
    for o in rows:
        other_id = o.member_b_id if o.member_a_id == member.id else o.member_a_id
        other = db.get(Member, other_id)
        overlaps.append(
            OverlapSchema(
                id=o.id,
                other_member=MemberLite.model_validate(other),
                kind=o.kind,
                strength=o.strength,
                place=PlaceSchema.model_validate(o.place) if o.place is not None else None,
                country_code=o.country_code,
                start_date=o.start_date,
                end_date=o.end_date,
            )
        )
    return {"overlaps": overlaps}
