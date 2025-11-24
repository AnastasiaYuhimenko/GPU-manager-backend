from functools import lru_cache

from app.core.config import settings
from redis.asyncio import Redis


@lru_cache
def get_redis() -> Redis:
    return Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=0,
        decode_responses=True,
    )


async def redis_dep() -> Redis:
    return get_redis()
