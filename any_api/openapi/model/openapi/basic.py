from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
