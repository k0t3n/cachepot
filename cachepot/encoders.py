from typing import Optional, Dict

from fastapi import Response
from pydantic import BaseModel


class ResponseEncoder(BaseModel):
    body: bytes
    status_code: int
    headers: Optional[Dict[str, str]]

    @classmethod
    def encode(cls, response: Response):
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
