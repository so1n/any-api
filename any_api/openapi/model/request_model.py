from typing import Dict, List, Optional, Type

from pydantic import BaseModel, Field

from .openapi_model import OperationModel, TagModel
from .response_model import BaseResponseModel
from .util import HttpMethodLiteral, HttpParamTypeLiteral


class RequestModel(BaseModel):
    media_type: str = Field("", description="OpenAPI media type")
    openapi_serialization: Optional[dict] = Field(None, description="OpenAPI serialization")
    model: Type[BaseModel] = Field(description="request model")


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
    http_method_list: List[HttpMethodLiteral] = Field()
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
    input_dict: Dict[HttpParamTypeLiteral, List[RequestModel]] = Field(default_factory=dict)
    output_list: List[Type[BaseResponseModel]] = Field(default_factory=list)

    def add_to_openapi_method_dict(self, openapi_model: OperationModel) -> None:
        pass
