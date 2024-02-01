from fastapi import Response
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders


class ResponseEncoder(BaseModel):
    body: bytes
    status_code: int
    headers: MutableHeaders

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
