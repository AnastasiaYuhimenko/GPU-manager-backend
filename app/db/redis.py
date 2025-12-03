from typing import Annotated

from app.core.config import settings
from fastapi import Depends
from redis.asyncio import Redis

redis_client: Redis | None = None


async def redis_dep() -> Redis:
    return redis_client


RedisDep = Annotated[Redis, Depends(redis_dep)]


async def connect_to_redis():
    global redis_client

    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=0,
        decode_responses=True,
    )

    try:
        await redis_client.ping()
    except Exception as exc:
        raise RuntimeError("Redis недоступен") from exc  # TODO: зачем это надо и привести пример


async def disconnect_from_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
