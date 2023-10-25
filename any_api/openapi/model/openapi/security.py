from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from any_api.base_api.model.base_api_model import BaseSecurityModel
from any_api.openapi.model.util import SecurityHttpParamTypeLiteral
from any_api.util import pydantic_adapter


class OAuthFlowModel(BaseModel):
    """https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#oauth-flow-object"""

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
    """https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#oauth-flows-object"""

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

    @pydantic_adapter.model_validator(mode="before")
    @classmethod
    def check_include_model(cls, values: Dict[str, OAuthFlowModel]) -> Dict[str, OAuthFlowModel]:
        for key, oauth_flow_model in values.items():
            if key in ("implicit", "authorizationCode"):
                if oauth_flow_model.authorization_url is None:
                    raise ValueError(f"{key}->{oauth_flow_model.__class__.__name__}->`authorizationUrl` not be empty")
            if key in ("authorizationCode", "password", "clientCredentials"):
                if oauth_flow_model.token_url is None:
                    raise ValueError(f"{key}->{oauth_flow_model.__class__.__name__}->`tokenUrl` not be empty")
        return values


class OpenIdConnectUrlSecurityModel(BaseSecurityModel):
    open_id_connect_url: str = Field(
        alias="openIdConnectUrl",
        description="OpenId Connect URL to discover OAuth2 configuration values. This MUST be in the form of a URL.",
    )

    @pydantic_adapter.model_validator(mode="before")
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "openIdConnect"
        return values


class Oauth2SecurityModel(BaseSecurityModel):
    flows: OAuthFlowsModel = Field(
        description="An object containing configuration information for the flow types supported."
    )

    @pydantic_adapter.model_validator(mode="before")
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


class UserScopesOauth2SecurityModel(Oauth2SecurityModel):
    use_scopes: List[str] = Field(description="Scope for the real use Oauth2SecurityModel", default_factory=list)
    model: Oauth2SecurityModel = Field(description="Parent Oauth2SecurityModel")

    @pydantic_adapter.model_validator(mode="before")
    @classmethod
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        model: Oauth2SecurityModel = values["model"]
        values["flows"] = model.flows
        all_scopes = model.get_security_scope()
        scopes = values["use_scopes"]
        _scopes_set = set(scopes) - set(all_scopes)
        if len(_scopes_set) > 0:
            raise ValueError(f"{_scopes_set} not in {all_scopes}")
        return values

    def get_security_scope(self) -> List[str]:
        if self.use_scopes:
            return self.use_scopes
        return self.model.get_security_scope()


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

    @pydantic_adapter.model_validator(mode="before")
    @classmethod
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "http"
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
        ),
        exclude=True,
    )

    @pydantic_adapter.model_validator(mode="before")
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["type"] = "apiKey"
        values["in"] = values["in_stub"]
        return values


SecurityModelType = Union[ApiKeySecurityModel, HttpSecurityModel, Oauth2SecurityModel, OpenIdConnectUrlSecurityModel]
