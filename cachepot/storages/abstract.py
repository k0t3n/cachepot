import abc
from typing import Optional


class AbstractStorage(abc.ABC):

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
