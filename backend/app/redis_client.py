from __future__ import annotations

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def redis_is_ready() -> bool:
    try:
        pong = await redis_client.ping()
        return bool(pong)
    except Exception:
        return False


async def close_redis() -> None:
    await redis_client.close()
