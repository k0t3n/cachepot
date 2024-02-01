from typing import Optional

from redis.asyncio.client import Redis

from cachepot.storages.abstract import AbstractStorage


class RedisStorage(AbstractStorage):
    def __init__(self, redis: Redis[bytes]):
        assert isinstance(redis, Redis), 'Invalid Redis client passed'
        self.redis: Redis[bytes] = redis

    async def get(self, key: str) -> Optional[bytes]:
        data = await self.redis.get(key)
        if data and not isinstance(data, bytes):
            return bytes(data)
        return None

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> bool:
        await self.redis.set(key, value, ex=expire)
        return True

    async def delete(self, key: str) -> bool:
        return bool(await self.redis.delete(key))
