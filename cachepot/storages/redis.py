from typing import Optional

from redis.asyncio.client import Redis

from cachepot.storages.abstract import AbstractStorage


class RedisStorage(AbstractStorage):
    def __init__(self, redis: Redis):
        assert isinstance(redis, Redis), 'Invalid Redis client passed'
        self.redis = redis

    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(key)

    async def set(self, key: str, value: bytes, expire: Optional[int] = None):
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        return await self.redis.delete(key)
