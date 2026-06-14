"""Member routes: own-profile edit, photo upload, directory, member detail."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session as DbSession

from catchup.api.schemas import MemberDetail, MemberSummary, ProfileUpdate
from catchup.auth.deps import get_current_member
from catchup.config import get_settings
from catchup.db import get_session
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
    data = await file.read()
    ext = validate_photo(file.content_type, len(data), data, settings.photo_allowed_types, settings.photo_max_bytes)
    key = f"members/{member.id}/avatar.{ext}"
    url = get_photo_store(settings).put(key, data, file.content_type)
    service.set_photo(db, member, url)
    return {"photo_url": url}


@router.delete("/me/photo", status_code=204)
def delete_photo(member: Member = Depends(get_current_member), db: DbSession = Depends(get_session)) -> None:
    settings = get_settings()
    if member.photo_url:
        key = member.photo_url.replace(settings.s3_public_base_url.rstrip("/") + "/", "")
        try:
            get_photo_store(settings).delete(key)
        except Exception:
            logger.warning("Failed to delete photo object %s", key, exc_info=True)
    service.clear_photo(db, member)
