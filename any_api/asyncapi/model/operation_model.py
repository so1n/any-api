from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ...openapi.model.openapi import TagModel
from ...openapi.model.openapi.basic import ExternalDocumentationModel


class OperationModel(BaseModel):
    operation_id: str = Field(
        default="",
        alias="operationId",
        description=(
            "Unique string used to identify the operation. "
            "The id MUST be unique among all operations described in the API. "
            "The operationId value is case-sensitive."
            "Tools and libraries MAY use the operationId to uniquely identify an operation, "
            "therefore, it is RECOMMENDED to follow common programming naming conventions."
        ),
    )
    summary: str = Field(default="", description="A short summary of what the operation is about.")
    description: str = Field(
        default="",
        description=(
            "A verbose explanation of the operation. CommonMark syntax can be used for rich text representation."
        ),
    )
    security: List[Dict[str, list]] = Field(
        default_factory=list,
        description=(
            "A declaration of which security mechanisms can be used with this server. "
            "The list of values includes alternative security requirement objects that can be used. "
            "Only one of the security requirement objects need to be satisfied to authorize a connection or operation."
        ),
    )
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
    external_docs: ExternalDocumentationModel = Field(
        alias="externalDocs", default_factory=dict, description="Additional external documentation for this tag."
    )
    bindings: Dict = Field(
        default_factory=dict,
        description=(
            "A map where the keys describe the name of the protocol and the values describe protocol-specific"
            " definitions for the server."
        ),
    )
    message: List[BaseModel] = Field(
        description=(
            "A definition of the message that will be published or received by this operation. "
            "Map containing a single oneOf key is allowed here to specify multiple messages. "
            "However, a message MUST be valid only against one of the message objects."
        )
    )


class ChannelItemModel(BaseModel):
    name: str
    parameters: Optional[BaseModel] = Field(
        default=None,
        description=(
            "A map of the parameters included in the channel name."
            " It SHOULD be present only when using channels with expressions (as defined by RFC 6570 section 2.2)."
        ),
    )
    description: str = Field(
        default="",
        description=(
            "A verbose explanation of the operation. CommonMark syntax can be used for rich text representation."
        ),
    )
    servers: List[str] = Field(
        default_factory=list,
        description=(
            "The servers on which this channel is available, "
            "specified as an optional unordered list of names (string keys) of Server Objects defined in the Servers"
            " Object (a map). If servers is absent or empty then this channel must be available on all servers defined"
            " in the Servers Object."
        ),
    )
    subscribe: Optional[OperationModel] = Field(
        default=None,
        description=(
            "A definition of the SUBSCRIBE operation, "
            "which defines the messages consumed by the application from the channel."
        ),
    )
    publish: Optional[OperationModel] = Field(
        default=None,
        description=(
            "A definition of the PUBLISH operation, "
            "which defines the messages consumed by the application from the channel."
        ),
    )
    bindings: Dict = Field(
        default_factory=dict,
        description=(
            "A map where the keys describe the name of the protocol and the values describe protocol-specific"
            " definitions for the server."
        ),
    )
