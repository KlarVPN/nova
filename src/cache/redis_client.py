import logging
from typing import Optional

import redis.asyncio as aioredis

from src.config import Settings

_redis_client: Optional[aioredis.Redis] = None


async def create_redis_client(settings: Settings) -> aioredis.Redis:
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=False,
    )
    try:
        await _redis_client.ping()
        logging.info("Redis connected: %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)
    except Exception as e:
        logging.error("Redis connection failed: %s", e)
        raise
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logging.info("Redis connection closed.")


def get_redis_client() -> Optional[aioredis.Redis]:
    return _redis_client
