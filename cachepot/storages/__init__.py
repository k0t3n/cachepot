__all__ = []

try:
    from cachepot.storages.redis import RedisStorage
except ImportError:
    pass
else:
    __all__ += ['RedisStorage']
