from typing import Any, Dict, Optional, Tuple, Type, Union

from pydantic import BaseModel
from any_api.util.by_pydantic import gen_example_dict_from_schema


__all__ = [
    "BaseResponseModel",
    "HtmlResponseModel",
    "JsonResponseModel",
    "FileResponseModel",
    "TextResponseModel",
]


class BaseResponseModel(object):
    """response model https://swagger.io/docs/specification/describing-responses/"""

    # response data
    response_data: Union[Type[BaseModel], str, bytes]
    # response media type
    media_type: str = "*/*"

    # response name
    name: Optional[str] = None
    # response description
    description: Optional[str] = None
    # response header
    header: dict = {}
    # response status code
    status_code: Tuple[int] = (200,)

    # The value of this response in openapi.schema
    # if value is empty,  will auto gen response model and set to openapi.schema
    openapi_schema: Optional[dict] = None

    # links model
    links_schema_dict: Dict[str, dict] = {}

    @classmethod
    def get_example_value(cls, **extra: Any) -> Any:
        return cls.response_data

    @classmethod
    def register_link_schema(cls, link_schema: dict) -> None:
        cls.links_schema_dict.update(link_schema)


class JsonResponseModel(BaseResponseModel):
    response_data: Type[BaseModel]
    media_type: str = "application/json"

    @classmethod
    def get_example_value(cls, **extra: Any) -> dict:
        return gen_example_dict_from_schema(cls.response_data.schema())


class TextResponseModel(BaseResponseModel):
    response_data: str = "example data"
    media_type: str = "text/plain"

    openapi_schema: dict = {"type": "string", "example": response_data}


class HtmlResponseModel(BaseResponseModel):
    response_data: str = "<h1> example html</h1>"
    media_type: str = "text/html"

    openapi_schema: dict = {"type": "string", "example": response_data}


class FileResponseModel(BaseResponseModel):
    response_data: bytes = b" example bytes"
    media_type: str = "application/octet-stream"

    openapi_schema: dict = {"type": "string", "format": "binary"}