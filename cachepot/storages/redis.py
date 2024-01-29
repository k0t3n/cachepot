from cachepot.storages.abstract import AbstractStorage
from redis.asyncio.client import Redis


class RedisStorage(AbstractStorage):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> bytes | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: bytes, expire: int | None = None):
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        return await self.redis.delete(key)
