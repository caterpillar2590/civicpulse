from __future__ import annotations

import hashlib
import os

from app.models.schemas import Category, Priority, TriageResult
from app.providers.triage.base import RetryableTriageError, TriageError

# Behaviour is controlled by env vars so CI can exercise every code path
# without network access or sleep()-based flakiness:
#   SIMULATED_TRIAGE_MODE = ok | timeout | malformed | http_error
SIM_MODE_ENV = "SIMULATED_TRIAGE_MODE"


class SimulatedTriage:
    name = "llm:simulated"

    async def triage(self, text: str, location: str) -> TriageResult:
        mode = os.getenv(SIM_MODE_ENV, "ok")

        if mode == "timeout" or mode == "http_error":
            raise RetryableTriageError(f"simulated {mode}")
        if mode == "malformed":
            raise TriageError("simulated malformed JSON from provider")

        # Deterministic pseudo-classification from a hash of the text, so the
        # same input always produces the same output -> a stable test fixture.
        digest = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        categories = list(Category)
        category = categories[digest % len(categories)]
        priority = list(Priority)[digest % 3]

        summary = text.strip().replace("\n", " ")[:137]
        if len(text.strip()) > 137:
            summary += "..."

        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=0.75,
        )
