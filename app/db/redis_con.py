from redis.asyncio import Redis

redis_client: Redis | None = None


def redis_dep() -> Redis:
    return redis_client
