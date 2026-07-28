"""
AION Redis Async Client
Caching, pub/sub, and session management
"""
from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


class CacheService:
    def __init__(self, redis: Redis, default_ttl: int = settings.REDIS_CACHE_TTL):
        self._redis = redis
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        value = await self._redis.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        serialized = json.dumps(value, default=str)
        expire = ttl if ttl is not None else self._default_ttl
        return await self._redis.set(key, serialized, ex=expire)

    async def delete(self, key: str) -> int:
        return await self._redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        return await self._redis.incrby(key, amount)

    async def expire(self, key: str, ttl: int) -> bool:
        return await self._redis.expire(key, ttl)

    async def publish(self, channel: str, message: Any) -> int:
        serialized = json.dumps(message, default=str)
        return await self._redis.publish(channel, serialized)

    async def get_or_set(self, key: str, factory: Any, ttl: Optional[int] = None) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory() if callable(factory) else factory
        await self.set(key, value, ttl)
        return value


async def get_cache_service() -> CacheService:
    redis = await get_redis()
    return CacheService(redis)
