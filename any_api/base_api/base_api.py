import copy
import json
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from typing_extensions import Self

from any_api.base_api.model.base_api_model import BaseAPIModel, BaseSecurityModel
from any_api.openapi.model.openapi import TagModel
from any_api.openapi.model.openapi.security import UserScopesOauth2SecurityModel
from any_api.util import pydantic_adapter

__all__ = ["BaseAPI"]

_ModelT = TypeVar("_ModelT", bound=BaseAPIModel)
_ApiModelT = TypeVar("_ApiModelT")


class BaseAPI(Generic[_ModelT, _ApiModelT]):
    _api_model: _ModelT
    _schema_key: str = "schemas"
    _add_tag_dict: dict = {}

    def __init__(self) -> None:
        self._temp_model_list: List[_ApiModelT] = []
        self._has_not_load_model: bool = False

        self._model_name_map: pydantic_adapter.ModelNameMapType = {}
        self._definitions: dict = {}
        self._model_use_count: Dict[Type[BaseModel], int] = {}

    def add_api_model(self, *api_model_list: _ApiModelT) -> "Self":
        for api_model in api_model_list:
            self._temp_model_list.append(api_model)
        self._has_not_load_model = True
        return self

    def generate(self) -> None:
        # The definition data must be reloaded each time the data is generated
        self._load_definitions_by_api_model()
        for api_model in self._temp_model_list:
            self._add_request_to_api_model(api_model)

    def _load_definitions_by_api_model(self) -> None:
        raise NotImplementedError

    def _add_request_to_api_model(self, api_model: _ApiModelT) -> "Self":
        raise NotImplementedError

    def _add_tag(self, *tag_list: TagModel) -> None:
        for tag in tag_list:
            if tag.name not in self._add_tag_dict:
                self._add_tag_dict[tag.name] = tag.description
                self._api_model.tags.append(tag)
            elif tag.description != self._add_tag_dict[tag.name]:
                raise ValueError(
                    f"tag:{tag.name} already exists, but the description of the tag is inconsistent"
                    f" with the current one"
                )

    def _add_security(self, security_model_dict: Dict[str, BaseSecurityModel]) -> None:
        if "securitySchemes" not in self._api_model.components:
            new_security_model_dict: Dict[str, BaseSecurityModel] = {}
            for security_key, security_model in security_model_dict.items():
                if isinstance(security_model, UserScopesOauth2SecurityModel):
                    security_model = security_model.model
                new_security_model_dict[security_key] = security_model
            self._api_model.components["securitySchemes"] = new_security_model_dict
        else:
            for security_key, security_model in security_model_dict.items():
                if isinstance(security_model, UserScopesOauth2SecurityModel):
                    security_model = security_model.model
                if security_key in self._api_model.components["securitySchemes"]:
                    if self._api_model.components["securitySchemes"][security_key] != security_model:
                        raise KeyError(f"{security_key} already exists, and the security model is the same")
                else:
                    self._api_model.components["securitySchemes"][security_key] = security_model

    def _replace_pydantic_definitions(self, schema: dict, parent_schema: Optional[dict] = None) -> None:
        """update schemas'definitions to components schemas"""
        if not parent_schema:
            parent_schema = schema
        for key, value in schema.items():
            if key == "$ref" and not value.startswith("#/components"):
                index: int = value.rfind("/") + 1
                model_key: str = value[index:]
                schema[key] = f"#/components/{self._schema_key}/{model_key}"
                self._api_model.components[self._schema_key][model_key] = parent_schema["definitions"][model_key]
            elif isinstance(value, dict):
                self._replace_pydantic_definitions(value, parent_schema)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._replace_pydantic_definitions(item, parent_schema)

    def _xml_handler(self, schema_dict: dict) -> None:
        """
        Add XML support for schemas in a traversal and recursive manner,
        the specific display method will be determined according to the media type,
        and will not affect the data display of application/json
        """
        if "xml" in schema_dict:
            return
        schema_dict["xml"] = {"name": schema_dict["title"]}
        if "properties" not in schema_dict:
            return
        for key, value in schema_dict["properties"].items():
            # nested schema handler
            if "$ref" in value:
                _, _, schema_key, key = value["$ref"].split("/")
                self._xml_handler(self._api_model.components[self._schema_key][key])

            # array handler
            if value.get("type", "") != "array":
                continue
            value["xml"] = {"wrapped": True}
            if "$ref" not in value["items"]:
                value["items"]["xml"] = {"name": value["title"]}
            else:
                _, _, schema_key, key = value["items"]["$ref"].split("/")
                self._xml_handler(self._api_model.components[self._schema_key][key])

    def _get_not_in_components_model_schema(self, model: Type[BaseModel]) -> dict:
        return pydantic_adapter.model_json_schema(model)

    def _get_in_components_model_schema(self, model: Type[BaseModel]) -> Tuple[str, dict]:
        global_model_name = self._model_name_map[model]
        schema_dict: dict = self._definitions[self._model_name_map[model]]
        return global_model_name, schema_dict

    def _schema_handle(
        self,
        model: Type[BaseModel],
        enable_move_to_component: bool = True,
        is_xml_model: bool = False,
    ) -> Tuple[str, dict]:
        from any_api.util import by_pydantic

        global_model_name = by_pydantic.get_model_global_name(model)

        if (
            global_model_name in self._api_model.components[self._schema_key]
            and enable_move_to_component
            and not is_xml_model
        ):
            return global_model_name, self._api_model.components[self._schema_key][global_model_name]
        schema_dict: dict = copy.deepcopy(by_pydantic.any_api_model_schema(model))
        if is_xml_model:
            self._xml_handler(schema_dict)
        self._replace_pydantic_definitions(schema_dict)
        if "definitions" in schema_dict:
            # fix del schema dict
            del schema_dict["definitions"]
        if enable_move_to_component:
            self._api_model.components[self._schema_key].update({global_model_name: schema_dict})
        return global_model_name, schema_dict

    def _get_real_schema_dict(self, schema_dict: dict) -> dict:
        if len(schema_dict) == 1 and "$ref" in schema_dict:
            _, _, schema_key, key = schema_dict["$ref"].split("/")
            return self._api_model.components[self._schema_key][key]
        else:
            return schema_dict

    @property
    def model(self) -> _ModelT:
        if self._has_not_load_model:
            self.generate()
            self._has_not_load_model = False
        return self._api_model

    @property
    def dict(self) -> dict:
        openapi_dict: dict = pydantic_adapter.model_dump(self.model, exclude_none=True, by_alias=True)
        # if not openapi_dict["info"]["terms_of_service"]:
        #     del openapi_dict["info"]["terms_of_service"]
        #
        # if not openapi_dict["info"]["content"]:
        #     del openapi_dict["info"]["license"]
        return openapi_dict

    def content(self, serialization_callback: Callable = json.dumps, **kwargs: Any) -> str:
        return serialization_callback(self.dict, **kwargs)
