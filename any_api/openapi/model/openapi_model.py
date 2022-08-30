from typing import Dict, List, Optional

from pydantic import AnyUrl, BaseModel, Field, HttpUrl

try:
    pass
except ImportError:
    EmailStr = str
else:
    from pydantic import EmailStr  # type: ignore


class Contact(BaseModel):
    name: str = Field(description="The identifying name of the contact person/organization.")
    url: AnyUrl = Field(description="The URL pointing to the contact information. MUST be in the format of a URL.")
    email: EmailStr = Field(
        description=("The email address of the contact person/organization. MUST be in the format of an email address.")
    )


class License(BaseModel):
    name: str = Field(description="The license name used for the API.")
    url: HttpUrl = Field(description="A URL to the license used for the API. MUST be in the format of a URL.")


class InfoModel(BaseModel):
    """open api info column model"""

    title: str = Field("AnyApi", description="The title of the API.")
    description: str = Field(
        "API Documentation",
        description="A short description of the API. CommonMark syntax MAY be used for rich text representation.",
    )
    terms_of_service: Optional[HttpUrl] = Field(
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
    url: HttpUrl = Field(
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
    variables: Dict[str, ServerVariableModel]


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
    external_docs: ExternalDocumentationModel = Field(
        alias="externalDocs", default_factory=dict, description="Additional external documentation for this tag."
    )


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
    paths: Dict = Field(default_factory=dict, description=" The available paths and operations for the API.")
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
    # TODO
    # "security": {},
    external_docs: ExternalDocumentationModel = Field(
        alias="externalDocs", default_factory=dict, description="Additional external documentation for this tag."
    )
