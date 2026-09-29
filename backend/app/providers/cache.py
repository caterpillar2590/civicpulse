from __future__ import annotations

import json
from typing import Any

from app.redis_client import redis_client

STATS_CACHE_KEY = "cache:stats:v1"
TRIAGE_CACHE_PREFIX = "cache:triage:"


async def get_stats_cache() -> tuple[dict[str, Any] | None, bool]:
    """Returns (value, hit)."""
    raw = await redis_client.get(STATS_CACHE_KEY)
    if raw is None:
        return None, False
    return json.loads(raw), True


async def set_stats_cache(value: dict[str, Any], ttl_seconds: int) -> None:
    await redis_client.set(STATS_CACHE_KEY, json.dumps(value), ex=ttl_seconds)


async def invalidate_stats_cache() -> None:
    """Called on every write so a new complaint is visible immediately, not up to TTL later."""
    await redis_client.delete(STATS_CACHE_KEY)


async def get_triage_cache(content_hash: str) -> dict[str, Any] | None:
    raw = await redis_client.get(TRIAGE_CACHE_PREFIX + content_hash)
    return json.loads(raw) if raw else None


async def set_triage_cache(content_hash: str, value: dict[str, Any], ttl_seconds: int) -> None:
    await redis_client.set(TRIAGE_CACHE_PREFIX + content_hash, json.dumps(value), ex=ttl_seconds)
