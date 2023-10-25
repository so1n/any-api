from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel
from typing_extensions import Literal

from any_api.openapi.model import openapi as openapi_model
from any_api.util.pydantic_adapter import gen_example_dict_from_schema, model_json_schema

__all__ = [
    "BaseResponseModel",
    "BaseOpenAPIResponseModel",
    "UnionResponseModel",
    "HtmlResponseModel",
    "JsonResponseModel",
    "FileResponseModel",
    "TextResponseModel",
    "XmlResponseModel",
]


_resp_model_class_link_dict: Dict[str, Dict[str, openapi_model.LinkModel]] = {}


class BaseOpenAPIResponseModel(object):
    # response description
    description: Optional[str] = None
    # response header
    header: Optional[Type[BaseModel]] = None
    # response status code
    status_code: Union[Tuple[int, ...], Literal["default"]] = (200,)


UnionResponseType = Type["BaseResponseModel"]


class UnionResponseModel(BaseOpenAPIResponseModel):
    response_list: Optional[List[UnionResponseType]] = None


def union(
    *response: UnionResponseType,
    description: Optional[str] = None,
    header: Optional[Type[BaseModel]] = None,
    status_code: Union[Tuple[int, ...], Literal["default"]] = (200,),
    ignore_attr_check: bool = False,
) -> "UnionResponseModel":
    if not ignore_attr_check:
        for item in response:
            for key in ("description", "header", "status_code"):
                if getattr(item, key, None):
                    raise ValueError(f"The union response model cannot set the `{key}` attribute.")
    param_dict = {"description": description, "header": header, "status_code": status_code, "response_list": response}
    return type(f"UnionResponseModel({param_dict})", (UnionResponseModel,), param_dict)  # type: ignore


class BaseResponseModel(BaseOpenAPIResponseModel):
    """response model https://swagger.io/docs/specification/describing-responses/"""

    # response data
    response_data: Union[Type[BaseModel], str, bytes, None] = None
    # response media type
    media_type: str = "*/*"

    # if response schema type is array, can set schema_type='array'
    schema_type: Optional[str] = None

    # The value of this response in openapi.schema
    # if value is empty,  will auto gen response model and set to openapi.schema
    openapi_schema: Optional[dict] = None

    @classmethod
    def _get_example_dict(cls, model: Type[BaseModel], **extra: Any) -> dict:
        return gen_example_dict_from_schema(model_json_schema(model))

    @classmethod
    def is_base_model_response_data(cls) -> bool:
        return isinstance(cls.response_data, type) and issubclass(cls.response_data, BaseModel)

    @classmethod
    def get_response_data_model(cls) -> Optional[Type[BaseModel]]:
        if cls.is_base_model_response_data():
            return cls.response_data  # type: ignore[return-value]
        return None

    @classmethod
    def get_example_value(cls, **extra: Any) -> Any:
        return cls.response_data

    @property
    def links_model_dict(self) -> Dict[str, openapi_model.LinkModel]:
        return _resp_model_class_link_dict.get(self.__class__.__qualname__, {})

    @classmethod
    def get_header_example_dict(cls, **extra: Any) -> dict:
        if not cls.header:
            return {}
        return cls._get_example_dict(cls.header, **extra)

    @classmethod
    def register_link_schema(cls, link_model_dict: Dict[str, openapi_model.LinkModel]) -> None:
        if cls.__qualname__ not in _resp_model_class_link_dict:
            _resp_model_class_link_dict[cls.__qualname__] = {}
        links_model_dict: Dict[str, openapi_model.LinkModel] = _resp_model_class_link_dict[cls.__qualname__]
        for key, value in link_model_dict.items():
            if key in links_model_dict:
                continue
            links_model_dict[key] = value


class JsonResponseModel(BaseResponseModel):
    response_data: Type[BaseModel]
    media_type: str = "application/json"

    @classmethod
    def get_example_value(cls, **extra: Any) -> dict:
        return cls._get_example_dict(cls.response_data, **extra)


class XmlResponseModel(JsonResponseModel):
    media_type: str = "application/xml"


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
