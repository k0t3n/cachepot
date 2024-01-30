from typing import Optional

from cachepot.storages.abstract import AbstractStorage


class DummyStorage(AbstractStorage):

    async def get(self, key: str) -> Optional[bytes]:
        return

    async def set(self, key: str, value: bytes, expire: Optional[int] = None):
        return

    async def delete(self, key: str):
        return
