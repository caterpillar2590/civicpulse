from __future__ import annotations

from typing import Protocol

from app.models.schemas import TriageResult


class TriageError(Exception):
    """Raised by a provider on failure (timeout, bad status, malformed output)."""


class RetryableTriageError(TriageError):
    """Timeout, 429, or 5xx — safe to retry once."""


class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult: ...
