"""Domain error type with a stable error code, mapped to the JSON error shape."""

from __future__ import annotations


class AppError(Exception):
    """An application error carrying a machine code and an HTTP status."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
