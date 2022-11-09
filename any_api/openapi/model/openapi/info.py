from typing import Optional

from pydantic import AnyUrl, BaseModel, Field

try:
    import email_validator  # isort: skip
except ImportError:
    EmailStr = str
else:
    from pydantic import EmailStr  # type: ignore


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
