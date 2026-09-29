from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.providers.cache import get_stats_cache, set_stats_cache
from app.repositories.complaint_repository import ComplaintRepository


async def get_stats(session: AsyncSession) -> tuple[dict, bool]:
    """Returns (stats, cache_hit)."""
    cached, hit = await get_stats_cache()
    if hit:
        return cached, True

    repo = ComplaintRepository(session)
    stats = await repo.stats()

    settings = get_settings()
    await set_stats_cache(stats, settings.stats_cache_ttl_seconds)
    return stats, False
