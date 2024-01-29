from cachepot.storages.abstract import AbstractStorage


class DummyStorage(AbstractStorage):

    async def get(self, key: str) -> bytes | None:
        return

    async def set(self, key: str, value: bytes, expire: int | None = None):
        return

    async def delete(self, key: str):
        return
