from dataclasses import dataclass
from typing import Callable, Optional, Union

from fastapi import Request

from cachepot.storages.abstract import AbstractStorage


@dataclass
class CachePolicy:
    storage: AbstractStorage
    key: Union[str, Callable[[Request], str]]
    is_active: bool = True
    ttl: Optional[int] = 30
    respect_no_cache: bool = True
    cached_response_header: str = 'X-Cache-Hit'

    def get_key(self, request: Request) -> str:
        return self.key if isinstance(self.key, str) else self.key(request=request)
