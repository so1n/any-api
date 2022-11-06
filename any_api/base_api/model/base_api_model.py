from typing import List

from pydantic import BaseModel, Field

from any_api.openapi.model.util import SecurityLiteral


class BaseAPIModel(BaseModel):
    openapi: str
    tags: list
    components: dict = Field(default_factory=dict)


class BaseSecurityModel(BaseModel):
    # The value will be forced to be set
    type_: SecurityLiteral = Field(
        default=None,
        alias="type",
        description='The type of the security scheme. Valid values are "apiKey", "http", "oauth2", "openIdConnect".',
    )
    description: str = Field(
        default="",
        description=(
            "A short description for security scheme. CommonMark syntax MAY be used for rich text representation."
        ),
    )

    def get_security_scope(self) -> List[str]:
        return []
