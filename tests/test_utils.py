from unittest.mock import patch

import pytest
from fastapi.requests import Request
from starlette.datastructures import MutableHeaders

from cachepot.constants import CachePolicy
from cachepot.encoders import ResponseEncoder
from cachepot.storages.dummy import DummyStorage
from cachepot.utils import is_cachable, get_cached_response


def test_is_cachable():
    assert is_cachable(
        request=Request(scope={'type': 'http', 'method': 'GET', 'headers': {}}),
        cache_policy=CachePolicy(storage=DummyStorage(), key='test')
    )


def test_is_cachable_incorrect_request_method():
    assert not is_cachable(
        request=Request(scope={'type': 'http', 'method': 'POST'}),
        cache_policy=CachePolicy(storage=DummyStorage(), key='test')
    )


def test_is_cachable_missing_cache_policy():
    assert not is_cachable(
        request=Request(scope={'type': 'http', 'method': 'GET'}),
        cache_policy=None
    )


def test_is_cachable_disabled_cache_policy():
    assert not is_cachable(
        request=Request(scope={'type': 'http', 'method': 'GET'}),
        cache_policy=CachePolicy(is_active=False, storage=DummyStorage(), key='test')
    )


@pytest.mark.parametrize(
    'cache_control, respect_no_cache, result',
    (
        (True, True, False),  # cache_control header provided and respected => pass
        (True, False, True),  # cache_control header provided, but not respected => cached
        (False, True, True),  # cache_control header not provided, but respected => cached
        (False, False, True),  # cache_control header not provided and not respected => cached
    )
)
def test_is_cachable_respect_no_cache(cache_control: bool, respect_no_cache: bool, result: bool):
    headers = []
    if cache_control:
        headers.append((b'cache-control', b'no-cache'))
    assert is_cachable(
        request=Request(scope={'type': 'http', 'method': 'GET', 'headers': headers}),
        cache_policy=CachePolicy(respect_no_cache=respect_no_cache, storage=DummyStorage(), key='test')
    ) is result


@pytest.mark.asyncio
async def test_get_cached_response_with_cache():
    with patch('cachepot.storages.dummy.DummyStorage.get') as mock_get_cache:
        headers = MutableHeaders({'test': 'test'})
        mock_get_cache.return_value = ResponseEncoder(
            body=b'{"hello": "world"}',
            status_code=200,
            headers=headers
        ).cache_data()
        response = await get_cached_response(
            request=Request(scope={'type': 'http', 'method': 'GET', 'headers': MutableHeaders()}),
            cache_policy=CachePolicy(storage=DummyStorage(), key='test')
        )

        assert response.body == b'{"hello": "world"}'
        assert response.status_code == 200
        assert response.headers == MutableHeaders({'test': 'test', 'x-cache-hit': 'true', 'content-length': '18'})


@pytest.mark.asyncio
async def test_get_cached_response_no_cache():
    with patch('cachepot.storages.dummy.DummyStorage.get') as mock_get_cache:
        mock_get_cache.return_value = None
        response = await get_cached_response(
            request=Request(scope={'type': 'http', 'method': 'GET', 'headers': []}),
            cache_policy=CachePolicy(storage=DummyStorage(), key='test')
        )

        assert response is None
