__all__ = []

try:
    from cachepot.storages import redis
except ImportError:
    pass
else:
    __all__ += ['redis']
