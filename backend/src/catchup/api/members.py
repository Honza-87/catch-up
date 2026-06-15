"""Member routes: own-profile edit, photo upload, directory, member detail."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import MemberDetail, MemberSummary, ProfileUpdate
from catchup.auth.deps import get_current_member
from catchup.config import get_settings
from catchup.db import get_session
from catchup.errors import AppError
from catchup.members import service
from catchup.members.validation import validate_photo
from catchup.models import Member
from catchup.storage import get_photo_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members", tags=["members"])


@router.get("")
def list_members(_: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    members = service.list_directory(db)
    return {"members": [MemberSummary.model_validate(m) for m in members]}


@router.get("/{member_id}")
def get_member(member_id: UUID, _: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> dict:
    return {"member": MemberDetail.model_validate(service.get_member(db, member_id))}


@router.get("/{member_id}/avatar")
def get_avatar(
    member_id: UUID,
    _: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> Response:
    """Stream a member's avatar from the private bucket. Session-gated, so the
    bucket never needs to be public."""
    member = db.get(Member, member_id)
    if member is None or not member.photo_key:
        raise AppError("not_found", "No photo.", status_code=404)
    data, content_type = get_photo_store(get_settings()).get(member.photo_key)
    return Response(content=data, media_type=content_type, headers={"Cache-Control": "private, max-age=3600"})


@router.patch("/me")
def update_me(
    body: ProfileUpdate,
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    updated = service.update_own_profile(db, member, body, get_settings())
    return {"member": MemberDetail.model_validate(updated)}


@router.post("/me/photo")
async def upload_photo(
    file: UploadFile = File(...),
    member: Member = Depends(get_current_member),
    db: DbSession = Depends(get_session),
) -> dict:
    settings = get_settings()
    # Reject oversized uploads before reading the whole body into memory.
    if file.size is not None and file.size > settings.photo_max_bytes:
        raise AppError("image_too_large", "Photo must be 5 MB or smaller.", 422)
    data = await file.read()
    ext = validate_photo(file.content_type, len(data), data, settings.photo_allowed_types, settings.photo_max_bytes)
    store = get_photo_store(settings)
    # Remove the previous object so a re-upload doesn't orphan it (the new key is
    # unique per upload, and the served URL's ?v= busts the browser cache).
    if member.photo_key:
        try:
            store.delete(member.photo_key)
        except Exception:
            logger.warning("Failed to delete old photo object %s", member.photo_key, exc_info=True)
    key = f"members/{member.id}/avatar-{uuid4().hex}.{ext}"
    store.put(key, data, file.content_type)
    service.set_photo(db, member, key)
    return {"photo_url": member.photo_url}


@router.delete("/me/photo", status_code=204)
def delete_photo(member: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> None:
    if member.photo_key:
        try:
            get_photo_store(get_settings()).delete(member.photo_key)
        except Exception:
            logger.warning("Failed to delete photo object %s", member.photo_key, exc_info=True)
    service.clear_photo(db, member)
