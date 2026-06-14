"""Geocoder interface + Photon (komoot) implementation.

Returns raw geocoder features; mapping to a Place is a pure step in parse.py.
"""

from __future__ import annotations

from typing import Protocol

import httpx


class Geocoder(Protocol):
    def search(self, query: str, limit: int = 8) -> list[dict]:
        """Return raw geocoder feature dicts for a free-text query."""
        ...


class PhotonGeocoder:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def search(self, query: str, limit: int = 8) -> list[dict]:
        resp = httpx.get(
            f"{self._base_url}/api",
            params={"q": query, "limit": limit, "layer": "city"},
            timeout=8.0,
        )
        resp.raise_for_status()
        return resp.json().get("features", [])
