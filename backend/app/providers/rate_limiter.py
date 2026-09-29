from __future__ import annotations

from app.redis_client import redis_client

# Why Redis and not an in-process dict: the moment the HPA scales the backend
# to N pods, an in-process counter permits N times the intended traffic.
# A fixed window keyed by client IP, shared across every pod, is what makes
# the limit actually mean what it says.

LUA_FIXED_WINDOW = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local current = redis.call("INCR", key)
if current == 1 then
    redis.call("EXPIRE", key, window)
end
local ttl = redis.call("TTL", key)
return {current, ttl}
"""


async def check_rate_limit(client_ip: str, window_seconds: int, max_requests: int) -> tuple[bool, int]:
    """Returns (allowed, retry_after_seconds)."""
    key = f"ratelimit:complaints:{client_ip}"
    script = redis_client.register_script(LUA_FIXED_WINDOW)
    current, ttl = await script(keys=[key], args=[window_seconds, max_requests])
    if current > max_requests:
        return False, max(ttl, 1)
    return True, 0
