"""Place routes (geocoder proxy). Endpoint added in US2."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/places", tags=["places"])
