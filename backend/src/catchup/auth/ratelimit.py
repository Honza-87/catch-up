"""Tiny in-memory fixed-window rate limiter for sign-in link requests.

Single-process only — adequate for a tens-of-users private app. A failed limit
raises AppError so the caller returns the same neutral response either way.
"""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_per_hour: int) -> None:
        self._max = max_per_hour
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, now: float | None = None) -> bool:
        """Record a hit for key; return True if still within the hourly budget."""
        now = now if now is not None else time.time()
        window_start = now - 3600
        hits = [t for t in self._hits[key] if t >= window_start]
        hits.append(now)
        self._hits[key] = hits
        return len(hits) <= self._max
