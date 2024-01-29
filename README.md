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
from fastapi import FastAPI, Depends

from cachepot.constants import CachePolicy
from cachepot.routing import CachedAPIRouter
from cachepot.storages.redis import RedisStorage

app = FastAPI()

app.router = CachedAPIRouter(
    dependency_overrides_provider=app,
    # define dependencies inside overridden router only
    dependencies=(Depends(...),),
)

# hack to finish setting up custom router
app.setup()

client = redis.from_url('redis://127.0.0.1:6379')
storage = RedisStorage(client)

cache_policy = CachePolicy(
    storage=storage,
    key='cached_hello_world',
    ttl=30,
)


# Do not use @app.route() due to incapability
@app.router.get(path='', cache_policy=cache_policy)
async def cached_hello_world():
    return {'result': 'hello, world!'}



```



