from typing import Dict, List

from pydantic import BaseModel, Field

from any_api.openapi.model.openapi import TagModel
from any_api.openapi.model.openapi.basic import ExternalDocumentationModel
from any_api.openapi.model.openapi.basic import ServerVariableModel as _ServerVariableModel
from any_api.openapi.model.openapi.metadata import InfoModel


class ServerVariableModel(_ServerVariableModel):
    examples: List[str] = Field(description="An array of examples of the server variable.")


class ServerModel(BaseModel):
    url: str = Field(
        description=(
            "A URL to the target host. This URL supports Server Variables and MAY be relative, "
            "to indicate that the host location is relative to the location"
            " where the OpenAPI document is being served. "
            "Variable substitutions will be made when a variable is named in { braces }."
        )
    )
    protocol: str = Field(
        description=(
            "The protocol this URL supports for connection. Supported protocol include,"
            " but are not limited to: amqp, amqps, http, https, ibmmq, jms, kafka, kafka-secure, anypointmq, mqtt, "
            " secure-mqtt, solace, stomp, stomps, ws, wss, mercure"
        )
    )
    protocol_version: str = Field(
        default="",
        alias="protocolVersion",
        description=(
            "The version of the protocol used for connection. For instance: AMQP 0.9.1, HTTP 2.0, Kafka 1.0.0, etc."
        ),
    )
    description: str = Field(
        default="",
        description=(
            "An optional string describing the host designated by the URL."
            " CommonMark syntax MAY be used for rich text representation."
        ),
    )
    variables: Dict[str, ServerVariableModel] = Field(
        default_factory=dict,
        description=(
            "A map between a variable name and its value."
            "The value is used for substitution in the server's URL template."
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
    bindings: Dict = Field(
        default_factory=dict,
        description=(
            "A map where the keys describe the name of the protocol and the values describe protocol-specific"
            " definitions for the server."
        ),
    )


class AsyncAPIModel(BaseModel):
    asyncapi: str = Field(
        "2.4.0",
        const=True,
        description=(
            "Specifies the AsyncAPI Specification version being used. "
            "It can be used by tooling Specifications and clients to interpret the version. "
            "The structure shall be major.minor.patch, where patch versions must be compatible "
            "with the existing major.minor tooling. "
            "Typically patch versions will be introduced to address errors in the documentation, "
            "and tooling should typically be compatible with the corresponding major.minor (1.0.*). "
            "Patch versions will correspond to patches of this document."
        ),
    )
    id_: str = Field(
        alias="id",
        description="Identifier of the application the AsyncAPI document is defining. "
        "(https://www.asyncapi.com/docs/reference/specification/v2.4.0#A2SIdString)",
    )
    info: InfoModel = Field(
        default_factory=InfoModel,
        description="Provides metadata about the API. The metadata can be used by the clients if needed.",
    )
    servers: Dict[str, ServerModel] = Field(
        default_factory=dict,
        description="The definition of a server this application MAY connect to",
    )
    default_content_type: str = Field(
        default="",
        alias="defaultContentType",
        description="Default content type to use when encoding/decoding a message's payload. eg.(application/json)",
    )
    channel: Dict = Field(default_factory=dict, description="The available channels and messages for the API.")
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
    components: Dict = Field(
        default_factory=lambda: {"schemas": {}}, description="An element to hold various schemas for the specification."
    )
    external_docs: ExternalDocumentationModel = Field(
        alias="externalDocs", default_factory=dict, description="Additional external documentation for this tag."
    )
