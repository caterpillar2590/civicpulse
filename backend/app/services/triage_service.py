from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.config import get_settings
from app.models.schemas import ProviderOutcome, TriageResult
from app.providers.cache import get_triage_cache, set_triage_cache
from app.providers.triage.base import RetryableTriageError, TriageError, TriageProvider
from app.providers.triage.factory import get_active_provider, get_fallback_provider
from app.middleware import TRIAGE_LATENCY, TRIAGE_FALLBACK_COUNT

logger = logging.getLogger("app.services.triage")


@dataclass
class TriageOutcome:
    result: TriageResult
    triaged_by: str
    latency_ms: int
    fallback: bool
    cache_hit: bool = False


# In-memory ring buffer backing GET /api/meta/providers ("last 20 outcomes").
# A single-process view is sufficient here; for multi-pod deployments this
# would move to Redis, but the observability *contract* stays the same.
_recent_outcomes: deque[ProviderOutcome] = deque(maxlen=20)
_cache_hits = 0
_cache_total = 0


def record_outcome(provider: str, latency_ms: int, fallback: bool) -> None:
    _recent_outcomes.appendleft(
        ProviderOutcome(
            provider=provider,
            latency_ms=latency_ms,
            fallback=fallback,
            timestamp=datetime.now(timezone.utc),
        )
    )


def get_recent_outcomes() -> list[ProviderOutcome]:
    return list(_recent_outcomes)


def get_triage_cache_hit_rate() -> float:
    return (_cache_hits / _cache_total) if _cache_total else 0.0


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


async def _call_with_retry(provider: TriageProvider, text: str, location: str, settings) -> TriageResult:
    try:
        return await asyncio.wait_for(
            provider.triage(text, location), timeout=settings.triage_timeout_seconds
        )
    except (asyncio.TimeoutError, RetryableTriageError):
        # Retry once, with jitter, only for retryable failures (timeout/429/5xx).
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return await asyncio.wait_for(
            provider.triage(text, location), timeout=settings.triage_timeout_seconds
        )


async def triage_complaint(text: str, location: str, complaint_id: str) -> TriageOutcome:
    global _cache_hits, _cache_total
    settings = get_settings()

    content_hash = _content_hash(text)
    _cache_total += 1
    cached = await get_triage_cache(content_hash)
    if cached is not None:
        _cache_hits += 1
        result = TriageResult.model_validate(cached["result"])
        return TriageOutcome(
            result=result,
            triaged_by=cached["triaged_by"],
            latency_ms=0,
            fallback=False,
            cache_hit=True,
        )

    provider = get_active_provider()
    start = time.monotonic()
    try:
        result = await _call_with_retry(provider, text, location, settings)
        latency_ms = int((time.monotonic() - start) * 1000)
        triaged_by = provider.name
        fallback = False
    except (TriageError, asyncio.TimeoutError) as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "triage fallback",
            extra={
                "extra_fields": {
                    "complaint_id": complaint_id,
                    "provider": provider.name,
                    "error_class": type(exc).__name__,
                }
            },
        )
        fallback_provider = get_fallback_provider()
        result = await fallback_provider.triage(text, location)
        triaged_by = "rules:fallback"
        fallback = True

    record_outcome(triaged_by, latency_ms, fallback)
    TRIAGE_LATENCY.observe(latency_ms / 1000)
    if fallback:
        TRIAGE_FALLBACK_COUNT.inc()

    if not fallback:
        await set_triage_cache(
            content_hash,
            {"result": result.model_dump(mode="json"), "triaged_by": triaged_by},
            settings.triage_cache_ttl_seconds,
        )

    return TriageOutcome(result=result, triaged_by=triaged_by, latency_ms=latency_ms, fallback=fallback)
