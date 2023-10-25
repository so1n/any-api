from typing import List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field

from any_api.openapi.model.openapi import EncodingModel


class RequestModel(BaseModel):
    #####################
    # request body info #
    #####################

    # If there are multiple RequestModels in ApiModel,
    # the data of the request body will only be obtained from the first `RequestModel` by default
    description: str = Field(
        default="",
        description=(
            "An optional description for the server variable. "
            "CommonMark syntax MAY be used for rich text representation."
            "Note: If the value is empty, it will get value by `RequestModel.__doc__`"
        ),
    )
    required: bool = Field(
        default=False, description="Determines if the request body is required in the request. Defaults to false."
    )

    ################
    # content info #
    ################
    media_type_list: List[str] = Field("", description="OpenAPI media type")
    openapi_serialization: Optional[EncodingModel] = Field(None, description="OpenAPI serialization")
    model: Union[Type[BaseModel], Tuple[Type[BaseModel], ...]] = Field(description="request model")

    # e.g:
    #   model schema:
    #       {
    #           'title': 'DynamicModel',
    #           'type': 'object',
    #           'properties': {'fake': {'title': 'Fake', 'format': 'binary', 'type': 'string'}},
    #           'required': ['fake']
    #       }
    #
    #   nested_model_key: fake
    #   get really schema:
    #       {'title': 'Fake', 'format': 'binary', 'type': 'string'}
    nested_model_key: Optional[str] = Field(
        default=None,
        description=(
            "Usually the schema of the Request Body is the schema of the model,"
            " but sometimes the schema of a field of the model is required"
        ),
    )
