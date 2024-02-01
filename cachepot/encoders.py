from typing import Any, Annotated

from fastapi import Response
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from starlette.datastructures import MutableHeaders


class _MutableHeadersTypeAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.dict_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(MutableHeaders),
                    core_schema.dict_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: dict(x)),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.dict_schema())


MutableHeadersType = Annotated[
    MutableHeaders, _MutableHeadersTypeAnnotation
]


class ResponseEncoder(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    body: bytes
    status_code: int
    headers: MutableHeadersType

    @classmethod
    def encode(cls, response: Response) -> 'ResponseEncoder':
        return ResponseEncoder(
            body=response.body,
            status_code=response.status_code,
            headers=response.headers
        )

    def decode(self) -> Response:
        return Response(
            content=self.body,
            status_code=self.status_code,
            headers=self.headers,
        )

    def cache_data(self) -> bytes:
        return self.model_dump_json().encode()
