"""
Redis client — shared singleton for pub/sub and caching.
"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def publish(channel: str, payload: Any) -> None:
    redis = await get_redis_client()
    if isinstance(payload, dict):
        payload = json.dumps(payload)
    await redis.publish(channel, payload)


async def set_cache(key: str, value: Any, ttl_s: int = 300) -> None:
    redis = await get_redis_client()
    if isinstance(value, dict):
        value = json.dumps(value)
    await redis.setex(key, ttl_s, value)


async def get_cache(key: str) -> Optional[str]:
    redis = await get_redis_client()
    return await redis.get(key)
