# Cachepot

![](https://github.com/k0t3n/cachepot/blob/main/docs/logo.png?raw=true)

The FastAPI cache the way it should be.

## Installation

```shell
pip install fastapi-cachepot
```

## Usage

```python
import redis.asyncio as redis

from cachepot.app import CachedFastAPI
from cachepot.constants import CachePolicy
from cachepot.storages import RedisStorage

app = CachedFastAPI()

client = redis.from_url('redis://127.0.0.1:6379')
storage = RedisStorage(client)

cache_policy = CachePolicy(
    storage=storage,
    key='cached_hello_world',
    ttl=30,
)


@app.get(path='', cache_policy=cache_policy)
async def cached_hello_world():
    return {'result': 'hello, world!'}

```



