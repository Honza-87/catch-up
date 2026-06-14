"""Member routes (directory + own profile). Endpoints added in US2/US3."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/members", tags=["members"])
