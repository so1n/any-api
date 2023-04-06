from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field, root_validator, validator

from any_api.base_api.model.base_api_model import BaseSecurityModel

from .links import LinksModel
from .openapi import OperationModel, TagModel
from .requests import RequestModel
from .responses import (
    BaseResponseModel,
    FileResponseModel,
    HtmlResponseModel,
    JsonResponseModel,
    TextResponseModel,
    XmlResponseModel,
)
from .util import HttpMethodLiteral, HttpParamTypeLiteral


class ApiModel(BaseModel):
    path: str = Field(
        description=(
            "A relative path to an individual endpoint. "
            "The field name MUST begin with a forward slash (/). "
            "The path is appended (no relative URL resolution) to the expanded URL from the Server Object's url field"
            " in order to construct the full URL. Path templating is allowed. When matching URLs, "
            "concrete (non-templated) paths would be matched before their templated counterparts. "
            "Templated paths with the same hierarchy but different templated names MUST NOT exist as they are "
            "identical. In case of ambiguous matching, it's up to the tooling to decide which one to use."
        )
    )
    http_method_list: List[HttpMethodLiteral] = Field(description="HTTP Method")
    tags: List[TagModel] = Field(
        default_factory=list,
        description=(
            "A list of tags used by the specification with additional metadata. "
            "The order of the tags can be used to reflect on their order by the parsing tools. "
            "Not all tags that are used by the Operation Object must be declared. "
            "The tags that are not declared MAY be organized randomly or based on the tools' logic. "
            "Each tag name in the list MUST be unique."
        ),
    )
    deprecated: bool = Field(
        False,
        description=(
            "Declares this operation to be deprecated. Consumers SHOULD refrain from usage of the declared operation. "
        ),
    )
    summary: str = Field(
        "", description="An optional, string summary, intended to apply to all operations in this path."
    )
    description: str = Field(
        "",
        description=(
            "An optional, string description, intended to apply to all operations in this path. "
            "CommonMark syntax MAY be used for rich text representation."
        ),
    )
    operation_id: str = Field(
        description=(
            "Unique string used to identify the operation. "
            "The id MUST be unique among all operations described in the API. "
            "The operationId value is case-sensitive. Tools and libraries MAY use the operationId to uniquely "
            "identify an operation, therefore, it is RECOMMENDED to follow common programming naming conventions."
        )
    )
    request_dict: Dict[HttpParamTypeLiteral, List[RequestModel]] = Field(
        default_factory=dict, description="request parameter and request body dict"
    )
    response_list: List[Union[Type[BaseResponseModel], Tuple[Type[BaseResponseModel]]]] = Field(
        default_factory=list, description="List of response object classes"
    )
    security: Optional[Dict[str, BaseSecurityModel]] = Field(
        default=None,
        description=(
            "Each name MUST correspond to a security scheme which is declared in the Security Schemes under the"
            ' Components Object. If the security scheme is of type "oauth2" or "openIdConnect",'
            " then the value is a list of scope names required for the execution, and the list MAY be empty "
            "if authorization does not require a specified scope. For other security scheme types,"
            " the array MUST be empty."
        ),
    )

    @validator("path")
    def validate_path(cls, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("path must start with `/`")
        return path

    @validator("response_list")
    def validate_core_response(
        cls, response_list: List[Union[Type[BaseResponseModel], Tuple[Type[BaseResponseModel]]]]
    ) -> List[Union[Type[BaseResponseModel], Tuple[Type[BaseResponseModel]]]]:
        cnt: int = 0
        for response in response_list:
            if isinstance(response, tuple):
                response = response[0]
            if response.is_core is True:
                cnt += 1
        if cnt > 1:
            raise ValueError("only one core response model")
        return response_list

    def add_to_operation_model(self, openapi_model: OperationModel) -> None:
        pass

    @root_validator
    def after_init(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Data association after initializing data"""
        if "request_dict" in values:
            request_dict: Dict[HttpParamTypeLiteral, List[RequestModel]] = values["request_dict"]
            for http_param_type_name, request_model_list in request_dict.items():
                for request_model in request_model_list:
                    if isinstance(request_model.model, tuple):
                        model_tuple: Tuple[Type[BaseModel]] = request_model.model
                    else:
                        model_tuple = (request_model.model,)
                    for model in model_tuple:
                        for field_name, field in model.__fields__.items():
                            if "links" in field.field_info.extra:
                                link_model: LinksModel = field.field_info.extra.pop("links")
                                link_model.register(
                                    param_name=field.field_info.alias or field_name,
                                    http_param_type_name=http_param_type_name,
                                    operation_id=values["operation_id"],
                                )
        return values
