from typing import Optional, List, Sequence, Callable, Any, Type, Dict, Union, TypeVar

from fastapi import FastAPI, routing
from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import Response
from fastapi.types import DecoratedCallable
from fastapi.utils import generate_unique_id
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute
from starlette.types import Lifespan

from cachepot.constants import CachePolicy
from cachepot.routing import CachedAPIRouter

AppType = TypeVar("AppType", bound="CachedFastAPI")


class CachedFastAPI(FastAPI):
    """The same FastAPI but with a router patch.

    TODO: temporary solution, fix when https://github.com/tiangolo/fastapi/pull/11053 merged
    """

    def __init__(
        self: AppType,
        *args: Any,
        routes: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        router_class: Type[routing.APIRouter] = CachedAPIRouter,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        dependencies: Optional[Sequence[Depends]] = None,
        lifespan: Optional[Lifespan[AppType]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        generate_unique_id_function: Callable[[routing.APIRoute], str] = Default(
            generate_unique_id
        ),
        **kwargs: Any
    ):
        super().__init__(
            *args,
            routes=routes,
            redirect_slashes=redirect_slashes,
            router_class=router_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            default_response_class=default_response_class,
            dependencies=dependencies,
            lifespan=lifespan,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
            **kwargs
        )
        self.router = router_class(
            routes=routes,
            redirect_slashes=redirect_slashes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
        )
        self.setup()

    def get(
        self,
        *args: Any,
        cache_policy: Optional[CachePolicy] = None,
        **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        if isinstance(self.router, CachedAPIRouter):
            return self.router.get(*args, cache_policy=cache_policy, **kwargs)
        return self.router.get(*args, **kwargs)


__all__ = ('CachedFastAPI',)
