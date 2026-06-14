"""Place routes: geocoder proxy for home-location autocomplete."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends

from catchup.auth.deps import get_current_member
from catchup.config import get_settings
from catchup.errors import AppError
from catchup.models import Member
from catchup.places.geocoder import PhotonGeocoder
from catchup.places.parse import features_to_places

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/search")
def search(q: str, _: Member = Depends(get_current_member)) -> dict:
    settings = get_settings()
    geocoder = PhotonGeocoder(settings.geocoder_url)
    try:
        features = geocoder.search(q)
    except httpx.HTTPError as exc:
        logger.warning("Geocoder unavailable: %s", exc)
        raise AppError(
            "geocoder_unavailable", "Place search is unavailable; enter city + country manually.", 502
        ) from exc
    return {"places": features_to_places(features)}
