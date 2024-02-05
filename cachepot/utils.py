import asyncio
import email
import json
from contextlib import AsyncExitStack
from typing import Optional, Union, Type, Any, Callable, Coroutine, Dict, cast

from fastapi import params
from fastapi._compat import ModelField, Undefined, _normalize_errors
from fastapi.datastructures import DefaultPlaceholder, Default
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import solve_dependencies
from fastapi.exceptions import RequestValidationError
from fastapi.routing import run_endpoint_function, serialize_response
from fastapi.types import IncEx
from fastapi.utils import is_body_allowed_for_status_code
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from cachepot.constants import CachePolicy
from cachepot.encoders import ResponseEncoder


def is_cachable(request: Request, cache_policy: Optional[CachePolicy]) -> bool:
    return bool(
        request.method == 'GET'
        and cache_policy
        and cache_policy.is_active
        and (not cache_policy.respect_no_cache or request.headers.get('cache-control') != 'no-cache')
    )


async def get_cached_response(request: Request, cache_policy: Optional[CachePolicy]) -> Optional[Response]:
    if is_cachable(request, cache_policy):
        policy = cast(CachePolicy, cache_policy)
        key = policy.get_key(request=request)
        if data := await policy.storage.get(key):
            response = ResponseEncoder.model_validate_json(data)
            if policy.cached_response_header:
                response.headers.update({policy.cached_response_header: 'true'})

            return response.decode()
    return None


async def cache_response(request: Request, response: Response, cache_policy: Optional[CachePolicy]) -> Response:
    if is_cachable(request, cache_policy):
        policy = cast(CachePolicy, cache_policy)
        response_data = ResponseEncoder.encode(response=response).cache_data()
        await policy.storage.set(key=policy.get_key(request), value=response_data, expire=policy.ttl)

        if policy.cached_response_header:
            response.headers.update({policy.cached_response_header: 'false'})

    return response


def get_request_handler(
    dependant: Dependant,
    body_field: Optional[ModelField] = None,
    status_code: Optional[int] = None,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    response_field: Optional[ModelField] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    dependency_overrides_provider: Optional[Any] = None,
    cache_policy: Optional[CachePolicy] = None,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    assert dependant.call is not None, 'dependant.call must be a function'
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(request: Request) -> Response:
        exception_to_reraise: Optional[Exception] = None
        response: Union[Response, None] = None
        async with AsyncExitStack() as async_exit_stack:
            # TODO: remove this scope later, after a few releases
            # This scope fastapi_astack is no longer used by FastAPI, kept for
            # compatibility, just in case
            request.scope['fastapi_astack'] = async_exit_stack
            try:
                body: Any = None
                if body_field:
                    if is_body_form:
                        body = await request.form()
                        async_exit_stack.push_async_callback(body.close)
                    else:
                        body_bytes = await request.body()
                        if body_bytes:
                            json_body: Any = Undefined
                            content_type_value = request.headers.get('content-type')
                            if not content_type_value:
                                json_body = await request.json()
                            else:
                                message = email.message.Message()
                                message['content-type'] = content_type_value
                                if message.get_content_maintype() == 'application':
                                    subtype = message.get_content_subtype()
                                    if subtype == 'json' or subtype.endswith('+json'):
                                        json_body = await request.json()
                            if json_body != Undefined:
                                body = json_body
                            else:
                                body = body_bytes
            except json.JSONDecodeError as e:
                validation_error = RequestValidationError(
                    [
                        {
                            'type': 'json_invalid',
                            'loc': ('body', e.pos),
                            'msg': 'JSON decode error',
                            'input': {},
                            'ctx': {'error': e.msg},
                        }
                    ],
                    body=e.doc,
                )
                exception_to_reraise = validation_error
                raise validation_error from e
            except HTTPException as e:
                exception_to_reraise = e
                raise
            except Exception as e:
                http_error = HTTPException(
                    status_code=400, detail='There was an error parsing the body'
                )
                exception_to_reraise = http_error
                raise http_error from e
            try:
                solved_result = await solve_dependencies(
                    request=request,
                    dependant=dependant,
                    body=body,
                    dependency_overrides_provider=dependency_overrides_provider,
                    async_exit_stack=async_exit_stack,
                )
                values, errors, background_tasks, sub_response, _ = solved_result
            except Exception as e:
                exception_to_reraise = e
                raise e
            if errors:
                validation_error = RequestValidationError(
                    _normalize_errors(errors), body=body
                )
                exception_to_reraise = validation_error
                raise validation_error
            else:
                if response := await get_cached_response(request, cache_policy):
                    return response

                try:
                    raw_response = await run_endpoint_function(
                        dependant=dependant, values=values, is_coroutine=is_coroutine
                    )
                except Exception as e:
                    exception_to_reraise = e
                    raise e
                if isinstance(raw_response, Response):
                    if raw_response.background is None:
                        raw_response.background = background_tasks
                    response = raw_response
                else:
                    response_args: Dict[str, Any] = {'background': background_tasks}
                    # If status_code was set, use it, otherwise use the default from the
                    # response class, in the case of redirect it's 307
                    current_status_code = (
                        status_code if status_code else sub_response.status_code
                    )
                    if current_status_code is not None:
                        response_args['status_code'] = current_status_code
                    if sub_response.status_code:
                        response_args['status_code'] = sub_response.status_code
                    content = await serialize_response(
                        field=response_field,
                        response_content=raw_response,
                        include=response_model_include,
                        exclude=response_model_exclude,
                        by_alias=response_model_by_alias,
                        exclude_unset=response_model_exclude_unset,
                        exclude_defaults=response_model_exclude_defaults,
                        exclude_none=response_model_exclude_none,
                        is_coroutine=is_coroutine,
                    )
                    response = actual_response_class(content, **response_args)
                    if not is_body_allowed_for_status_code(response.status_code):
                        response.body = b''
                    response.headers.raw.extend(sub_response.headers.raw)
        # This exception was possibly handled by the dependency but it should
        # still bubble up so that the ServerErrorMiddleware can return a 500
        # or the ExceptionMiddleware can catch and handle any other exceptions
        if exception_to_reraise:
            raise exception_to_reraise
        assert response is not None, 'An error occurred while generating the request'
        return await cache_response(request, response, cache_policy)

    return app

