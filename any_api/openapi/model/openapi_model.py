"""
pydantic.Base Model to store Open API objects

refer to: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md
"""
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, root_validator
from typing_extensions import Literal

from any_api.base_api.model.base_api_model import BaseSecurityModel

try:
    import email_validator  # isort: skip
except ImportError:
    EmailStr = str
else:
    from pydantic import EmailStr  # type: ignore

from .util import HttpMethodLiteral, SecurityHttpParamTypeLiteral


class Contact(BaseModel):
    name: str = Field(default="", description="The identifying name of the contact person/organization.")
    url: AnyUrl = Field(
        default="", description="The URL pointing to the contact information. MUST be in the format of a URL."
    )
    email: EmailStr = Field(
        description="The email address of the contact person/organization. MUST be in the format of an email address."
    )


class License(BaseModel):
    name: str = Field(description="The license name used for the API.")
    url: str = Field(description="A URL to the license used for the API. MUST be in the format of a URL.")


class InfoModel(BaseModel):
    """open api info column model"""

    title: str = Field("AnyApi", description="The title of the API.")
    description: str = Field(
        "API Documentation",
        description="A short description of the API. CommonMark syntax MAY be used for rich text representation.",
    )
    terms_of_service: Optional[str] = Field(
        None,
        alias="termsOfService",
        description="	A URL to the Terms of Service for the API. MUST be in the format of a URL.",
    )
    contact: Optional[Contact] = Field(None, description="The contact information for the exposed API.")
    license: Optional[License] = Field(None, description="The license information for the exposed API.")
    version: str = Field(
        "0.0.1",
        description=(
            "The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or "
            "the API implementation version)."
        ),
    )


class ServerVariableModel(BaseModel):
    enum: List[str] = Field(
        default_factory=list,
        description="An enumeration of string values to be used if the substitution options are from a limited set.",
    )
    default: str = Field(
        description="The default value to use for substitution, and to send, if an alternate value is not supplied."
    )
    description: str = Field(
        description=(
            "An optional description for the server variable. "
            "CommonMark syntax MAY be used for rich text representation."
        )
    )


class ServerModel(BaseModel):
    url: str = Field(
        description=(
            "A URL to the target host. This URL supports Server Variables and MAY be relative, "
            "to indicate that the host location is relative to the location"
            " where the OpenAPI document is being served. "
            "Variable substitutions will be made when a variable is named in {brackets}."
        )
    )
    description: str = Field(
        default="",
        description=(
            "An optional string describing the host designated by the URL."
            " CommonMark syntax MAY be used for rich text representation."
        ),
    )
    variables: Optional[Dict[str, ServerVariableModel]] = Field(default=None)


class ExternalDocumentationModel(BaseModel):
    description: str = Field(
        default="",
        description=(
            "A short description of the target documentation. "
            "CommonMark syntax MAY be used for rich text representation."
        ),
    )
    url: str = Field(description="The URL for the target documentation. Value MUST be in the format of a URL.")


class TagModel(BaseModel):
    name: str = Field(description="The name of the tag.")
    description: str = Field(
        "", description="A short description for the tag. CommonMark syntax MAY be used for rich text representation."
    )
    external_docs: Optional[ExternalDocumentationModel] = Field(
        alias="externalDocs", default=None, description="Additional external documentation for this tag."
    )


class RefModel(BaseModel):
    ref: str = Field(alias="$ref")


class ExampleModel(BaseModel):
    summary: str = Field(default="", description="A short summary of what the operation does.")
    description: str = Field(
        default="",
        description=(
            "A verbose explanation of the operation behavior. CommonMark syntax MAY be used for"
            " rich text representation."
        ),
    )
    value: Any = Field(
        description=(
            "Embedded literal example. The value field and externalValue field are mutually exclusive."
            " To represent examples of media types that cannot naturally represented in JSON or YAML, "
            "use a string value to contain the example, escaping where necessary."
        )
    )
    externalValue: str = Field(
        description=(
            "A URL that points to the literal example. This provides the capability to reference examples that"
            " cannot easily be included in JSON or YAML documents. The value field and externalValue field are "
            "mutually exclusive."
        )
    )


class HeaderModel(BaseModel):
    description: str = Field(
        default="",
        description=(
            "A brief description of the parameter. This could contain examples of use. "
            "CommonMark syntax MAY be used for rich text representation."
        ),
    )
    required: bool = Field(
        default=False,
        description=(
            'Determines whether this parameter is mandatory. If the parameter location is "path", '
            "this property is REQUIRED and its value MUST be true. Otherwise, the property MAY be included and its"
            " default value is false."
        ),
    )
    deprecated: bool = Field(
        default=False,
        description=(
            "Specifies that a parameter is deprecated and SHOULD be transitioned out of usage. Default value is false."
        ),
    )
    example: Any = Field(
        default=None,
        description=(
            "Example of the parameter's potential value. The example SHOULD match the specified schema and encoding"
            " properties if present. The example field is mutually exclusive of the examples field. Furthermore, "
            "if referencing a schema that contains an example, the example value SHALL override the example provided by"
            " the schema. To represent examples of media types that cannot naturally be represented in JSON or YAML,"
            " a string value can contain the example with escaping where necessary."
        ),
    )
    examples: Optional[Dict[str, Union[ExampleModel, RefModel]]] = Field(
        default=None,
        description=(
            "Examples of the parameter's potential value. Each example SHOULD contain a value in the correct format"
            " as specified in the parameter encoding. The examples field is mutually exclusive of the example field."
            " Furthermore, if referencing a schema that contains an example, "
            "the examples value SHALL override the example provided by the schema."
        ),
    )
    schema_: Union[RefModel, dict] = Field(
        alias="schema",
        # Do not create model the schema, facilitate subsequent expansion
        description="The schema defining the type used for the parameter.",
    )
    explode: bool = Field(
        default=False,
        description=(
            "When this is true, parameter values of type array or object generate separate parameters for each value "
            "of the array or key-value pair of the map. For other types of parameters this property has no effect. "
            "When style is form, the default value is true. For all other styles, the default value is false."
        ),
    )


class ParameterModel(HeaderModel):
    name: str = Field(
        description=(
            "The name of the parameter. Parameter names are case sensitive.\n"
            '- If in is "path", the name field MUST correspond to a template expression occurring within the path '
            "field in the Paths Object. See Path Templating for further information.\n"
            '- If in is "header" and the name field is "Accept", "Content-Type" or "Authorization", the parameter'
            "definition SHALL be ignored. For all other cases, the name corresponds to the parameter name used by the"
            " in property. "
        )
    )
    in_: Literal["query", "header", "path", "cookie"] = Field(
        default="",
        alias="in",
        description='The location of the parameter. Possible values are "query", "header", "path" or "cookie".',
    )
    in_stub: Literal["query", "header", "path", "cookie"] = Field(
        description=(
            "This value is a stand-in for `in`, and the value is automatically synchronized to `in` when initialized"
        )
    )

    class Config:
        fields = {"in_stub": {"exclude": True}}

    @root_validator(pre=True)
    def set_in(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["in"] = values["in_stub"]
        return values


class EncodingModel(BaseModel):
    content_type: str = Field(
        default="",
        alias="contentType",
        description=(
            "The Content-Type for encoding a specific property. Default value depends on the property type: "
            "for string with format being binary – application/octet-stream; for other primitive types – text/plain; "
            "for object - application/json; for array – the default is defined based on the inner type. "
            "The value can be a specific media type (e.g. application/json), a wildcard media type (e.g. image/*),"
            " or a comma-separated list of the two types."
        ),
    )
    headers: Dict[str, Union[RefModel, HeaderModel]] = Field(
        default_factory=dict,
        description=(
            "A map allowing additional information to be provided as headers, for example Content-Disposition."
            " Content-Type is described separately and SHALL be ignored in this section."
            " This property SHALL be ignored if the request body media type is not a multipart."
        ),
    )
    style: str = Field(
        default="",
        description=(
            "Describes how a specific property value will be serialized depending on its type. "
            "See Parameter Object for details on the style property. "
            "The behavior follows the same values as query parameters, including default values. "
            "This property SHALL be ignored if the request body media type is not application/x-www-form-urlencoded."
        ),
    )
    explode: bool = Field(
        default=False,
        description=(
            "When this is true, property values of type array or object generate separate parameters for each value of"
            " the array, or key-value-pair of the map. For other types of properties this property has no effect."
            "When style is form, the default value is true. For all other styles, the default value is false. "
            "This property SHALL be ignored if the request body media type is not application/x-www-form-urlencoded."
        ),
    )


class MediaTypeModel(BaseModel):
    schema_: Union[dict, RefModel] = Field(
        default_factory=dict,
        alias="schema",
        # Do not create model the schema, facilitate subsequent expansion
        description="The schema defining the type used for the parameter.",
    )
    example: Any = Field(
        default=None,
        description=(
            "Example of the parameter's potential value. The example SHOULD match the specified schema and encoding"
            " properties if present. The example field is mutually exclusive of the examples field. Furthermore, "
            "if referencing a schema that contains an example, the example value SHALL override the example provided by"
            " the schema. To represent examples of media types that cannot naturally be represented in JSON or YAML,"
            " a string value can contain the example with escaping where necessary."
        ),
    )
    examples: Optional[Dict[str, Union[ExampleModel, RefModel]]] = Field(
        default=None,
        description=(
            "Examples of the parameter's potential value. Each example SHOULD contain a value in the correct format"
            " as specified in the parameter encoding. The examples field is mutually exclusive of the example field."
            " Furthermore, if referencing a schema that contains an example, "
            "the examples value SHALL override the example provided by the schema."
        ),
    )
    encoding: Optional[Dict[str, EncodingModel]] = Field(
        default=None,
        description=(
            "A map between a property name and its encoding information. The key, being the property name, "
            "MUST exist in the schema as a property. The encoding object SHALL only apply to requestBody objects when"
            " the media type is multipart or application/x-www-form-urlencoded."
        ),
    )


class RequestBodyModel(BaseModel):
    description: str = Field(
        default="",
        description=(
            "An optional description for the server variable. "
            "CommonMark syntax MAY be used for rich text representation."
        ),
    )
    required: bool = Field(
        default=False, description="Determines if the request body is required in the request. Defaults to false."
    )
    content: Dict[str, MediaTypeModel] = Field(
        default_factory=dict,
        description=(
            "REQUIRED. The content of the request body. The key is a media type or media type range and the value "
            "describes it. For requests that match multiple keys, only the most specific key is applicable."
            " e.g. text/plain overrides text/*"
        ),
    )


class LinkModel(BaseModel):
    operation_ref: str = Field(
        alias="operationRef",
        description=(
            "A relative or absolute URI reference to an OAS operation. "
            "This field is mutually exclusive of the operationId field, and MUST point to an Operation Object."
            " Relative operationRef values MAY be used to locate an existing Operation Object in the OpenAPI"
            " definition."
        ),
    )
    operation_id: str = Field(
        alias="operationId",
        description=(
            "The name of an existing, resolvable OAS operation, as defined with a unique operationId."
            " This field is mutually exclusive of the operationRef field."
        ),
    )
    parameters: Dict[str, str] = Field(
        description=(
            "A map representing parameters to pass to an operation as specified with operationId or identified via"
            " operationRef. "
            "The key is the parameter name to be used, whereas the value can be a constant or an expression to be"
            " evaluated and passed to the linked operation. The parameter name can be qualified using the parameter"
            " location [{in}.]{name} for operations that use the same parameter name in different"
            " locations (e.g. path.id)."
        )
    )
    requestBody: str = Field(
        description="A literal value or {expression} to use as a request body when calling the target operation."
    )
    description: str = Field(
        description=(
            "An optional description for the server variable. "
            "CommonMark syntax MAY be used for rich text representation."
        )
    )
    server: ServerModel = Field(description="A server object to be used by the target operation.")


class ResponseModel(BaseModel):
    description: str = Field(
        description=(
            "An optional description for the server variable. "
            "CommonMark syntax MAY be used for rich text representation."
        )
    )
    headers: Optional[Dict[str, Union[RefModel, HeaderModel]]] = Field(
        default=None,
        description=(
            "Maps a header name to its definition. RFC7230 states header names are case insensitive. "
            'If a response header is defined with the name "Content-Type", it SHALL be ignored.'
        ),
    )
    content: Optional[Dict[str, MediaTypeModel]] = Field(
        default=None,
        description=(
            "REQUIRED. The content of the request body. The key is a media type or media type range and the value "
            "describes it. For requests that match multiple keys, only the most specific key is applicable."
            " e.g. text/plain overrides text/*"
        ),
    )
    links: Optional[Dict[str, Union[RefModel, LinkModel]]] = Field(
        default=None,
        description=(
            "A map of operations links that can be followed from the response. "
            "The key of the map is a short name for the link, following the naming constraints of the names for"
            " Component Objects."
        ),
    )


class OperationModel(BaseModel):
    tags: List[str] = Field(
        default_factory=list,
        description=(
            "A list of tags for API documentation control. "
            "Tags can be used for logical grouping of operations by resources or any other qualifier."
        ),
    )
    summary: str = Field(default="", description="A short summary of what the operation does.")
    description: str = Field(
        default="",
        description=(
            "A verbose explanation of the operation behavior."
            " CommonMark syntax MAY be used for rich text representation."
        ),
    )
    external_docs: Optional[ExternalDocumentationModel] = Field(
        alias="externalDocs", default=None, description="Additional external documentation for this tag."
    )
    operation_id: str = Field(
        alias="operationId",
        description=(
            "Unique string used to identify the operation. The id MUST be unique among all operations described in "
            "the API. The operationId value is case-sensitive. Tools and libraries MAY use the operationId to uniquely"
            " identify an operation, therefore, it is RECOMMENDED to follow common programming naming conventions."
        ),
    )
    parameters: List[Union[RefModel, ParameterModel]] = Field(
        default_factory=list,
        description=(
            "A list of parameters that are applicable for this operation. If a parameter is already defined at the "
            "Path Item, the new definition will override it but can never remove it. The list MUST NOT include"
            " duplicated parameters. A unique parameter is defined by a combination of a name and location. "
            "The list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's "
            "components/parameters."
        ),
    )
    request_body: Union[RefModel, RequestBodyModel, None] = Field(
        default=None,
        alias="requestBody",
        description=(
            "The request body applicable for this operation. "
            "The requestBody is only supported in HTTP methods where the HTTP 1.1 specification RFC7231 has explicitly"
            " defined semantics for request bodies. In other cases where the HTTP spec is vague, "
            "requestBody SHALL be ignored by consumers."
        ),
    )
    responses: Dict[str, ResponseModel] = Field(
        default_factory=dict,
        description="The list of possible responses as they are returned from executing this operation.",
    )
    # TODO callback
    # callbacks: Dict[str, Union[RefModel, ]] = Field(
    #     description=(
    #         "A map of possible out-of band callbacks related to the parent operation."
    #         " The key is a unique identifier for the Callback Object."
    #         " Each value in the map is a Callback Object that describes a request that may be initiated by the API"
    #         " provider and the expected responses."
    #     )
    # )
    deprecated: bool = Field(
        default=False,
        description=(
            "Specifies that a parameter is deprecated and SHOULD be transitioned out of usage. Default value is false."
        ),
    )
    security: Optional[List[Dict[str, List[str]]]] = Field(
        default=None,
        description=(
            "Each name MUST correspond to a security scheme which is declared in the Security Schemes under the"
            ' Components Object. If the security scheme is of type "oauth2" or "openIdConnect",'
            " then the value is a list of scope names required for the execution, and the list MAY be empty "
            "if authorization does not require a specified scope. For other security scheme types,"
            " the array MUST be empty."
        ),
    )
    servers: Optional[List[ServerModel]] = Field(
        default=None,
        description=(
            "An array of Server Objects, which provide connectivity information to a target server. "
            "If the servers property is not provided, or is an empty array, "
            "the default value would be a Server Object with a url value of /."
        ),
    )


class OAuthFlowModel(BaseModel):
    authorization_url: Optional[str] = Field(
        default=None,
        alias="authorizationUrl",
        description="The authorization URL to be used for this flow. This MUST be in the form of a URL.",
    )
    token_url: Optional[str] = Field(
        default=None,
        alias="tokenUrl",
        description="The token URL to be used for this flow. This MUST be in the form of a URL.",
    )
    refresh_url: Optional[str] = Field(
        default=None,
        alias="refreshUrl",
        description="The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL.",
    )
    scopes: Dict[str, str] = Field(
        description=(
            "The available scopes for the OAuth2 security scheme. A map between the scope name and a short description"
            " for it. The map MAY be empty."
        )
    )


class OAuthFlowsModel(BaseModel):
    implicit: Optional[OAuthFlowModel] = Field(default=None, description="Configuration for the OAuth Implicit flow")
    password: Optional[OAuthFlowModel] = Field(
        default=None, description="Configuration for the OAuth Resource Owner Password flow"
    )
    client_credentials: Optional[OAuthFlowModel] = Field(
        alias="clientCredentials",
        default=None,
        description=(
            "Configuration for the OAuth Client Credentials flow. Previously called application in OpenAPI 2.0."
        ),
    )
    authorization_code: Optional[OAuthFlowModel] = Field(
        alias="authorizationCode",
        default=None,
        description="Configuration for the OAuth Authorization Code flow. Previously called accessCode in OpenAPI 2.0.",
    )

    @root_validator(pre=True)
    def check_include_model(cls, values: Dict[str, OAuthFlowModel]) -> Dict[str, OAuthFlowModel]:
        for key, oauth_flow_model in values.items():
            if key in ("implicit", "authorizationCode"):
                if oauth_flow_model.authorization_url is None:
                    raise ValueError(f"{key}->{oauth_flow_model.__class__.__name__}->`authorizationUrl` not be empty")
            if key in ("authorizationCode", "password", "clientCredentials"):
                if oauth_flow_model.token_url is None:
                    raise ValueError(f"{key}->{oauth_flow_model.__class__.__name__}->`tokenUrl` not be empty")
        return values


class ApiKeySecurityModel(BaseSecurityModel):
    name: str = Field(description="The name of the header, query or cookie parameter to be used.")
    in_: SecurityHttpParamTypeLiteral = Field(
        default="",
        alias="in",
        description=' The location of the API key. Valid values are "query", "header" or "cookie".',
    )
    in_stub: SecurityHttpParamTypeLiteral = Field(
        description=(
            "This value is a stand-in for `in`, and the value is automatically synchronized to `in` when initialized"
        )
    )

    class Config:
        fields = {"in_stub": {"exclude": True}}

    @root_validator(pre=True)
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "apiKey"
        values["in"] = values["in_stub"]
        return values


class HttpSecurityModel(BaseSecurityModel):
    scheme: str = Field(
        description=(
            "The name of the HTTP Authorization scheme to be used in the Authorization header as defined in RFC7235. "
            "The values used SHOULD be registered in the IANA Authentication Scheme registry."
        )
    )
    bearer_format: Optional[str] = Field(
        default=None,
        alias="bearerFormat",
        description=(
            "A hint to the client to identify how the bearer token is formatted. Bearer tokens are usually generated by"
            " an authorization server, so this information is primarily for documentation purposes."
        ),
    )

    @root_validator(pre=True)
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "http"
        return values


class Oauth2SecurityModel(BaseSecurityModel):
    flows: OAuthFlowsModel = Field(
        description="An object containing configuration information for the flow types supported."
    )

    @root_validator(pre=True)
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "oauth2"
        return values

    def get_security_scope(self) -> List[str]:
        scope_list: List[str] = []
        if self.flows.authorization_code:
            scope_list.extend(self.flows.authorization_code.scopes.keys())

        if self.flows.client_credentials:
            scope_list.extend(self.flows.client_credentials.scopes.keys())

        if self.flows.implicit:
            scope_list.extend(self.flows.implicit.scopes.keys())

        if self.flows.password:
            scope_list.extend(self.flows.password.scopes.keys())
        return scope_list


class OpenIdConnectUrlSecurityModel(BaseSecurityModel):
    open_id_connect_url: str = Field(
        alias="openIdConnectUrl",
        description="OpenId Connect URL to discover OAuth2 configuration values. This MUST be in the form of a URL.",
    )

    @root_validator(pre=True)
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "openIdConnect"
        return values


SecurityModelType = Union[ApiKeySecurityModel, HttpSecurityModel, Oauth2SecurityModel, OpenIdConnectUrlSecurityModel]


class OpenAPIModel(BaseModel):
    openapi: str = Field(
        "3.0.0",
        const=True,
        description=(
            "This string MUST be the semantic version number of the OpenAPI Specification version that the OpenAPI"
            " document uses. The openapi field SHOULD be used by tooling specifications and clients to interpret"
            " the OpenAPI document. This is not related to the API info.version string."
        ),
    )
    info: InfoModel = Field(
        default_factory=InfoModel,
        description="Provides metadata about the API. The metadata MAY be used by tooling as required.",
    )
    servers: List[ServerModel] = Field(
        default_factory=list,
        description=(
            "An array of Server Objects, which provide connectivity information to a target server. "
            "If the servers property is not provided, or is an empty array, "
            "the default value would be a Server Object with a url value of /."
        ),
    )
    paths: Dict[str, Dict[HttpMethodLiteral, OperationModel]] = Field(
        default_factory=dict, description=" The available paths and operations for the API."
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
    components: Dict = Field(
        default_factory=lambda: {"schemas": {}}, description="An element to hold various schemas for the specification."
    )
    # This method will cover all, not flexible
    # security: Optional[List[SecurityModel]] = Field(
    #     default=None,
    #     description=(
    #         "A declaration of which security mechanisms can be used across the API. "
    #         "The list of values includes alternative security requirement objects that can be used. "
    #         "Only one of the security requirement objects need to be satisfied to authorize a request. "
    #         "Individual operations can override this definition. "
    #         "To make security optional, an empty security requirement ({}) can be included in the array."
    #     ),
    # )
    external_docs: ExternalDocumentationModel = Field(
        alias="externalDocs", default_factory=dict, description="Additional external documentation for this tag."
    )
