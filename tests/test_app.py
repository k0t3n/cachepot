import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from cachepot.app import CachedFastAPI
from cachepot.routing import CachedAPIRouter


@pytest.mark.parametrize(
    'router_class, expected_router_class',
    ((CachedAPIRouter, CachedAPIRouter), (APIRouter, APIRouter), (None, CachedAPIRouter)),
)
def test(router_class, expected_router_class):
    """Test CachedFastAPI can work both with APIRouter and CachedAPIRouter"""
    if router_class:
        app = CachedFastAPI(router_class=router_class)
    else:
        app = CachedFastAPI()
    assert isinstance(app.router, expected_router_class)

    @app.get('/')
    def hello_world():
        return {'hello': 'world'}

    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'hello': 'world'}
