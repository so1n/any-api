import copy
import json
from typing import Any, Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from any_api.base_api.model.base_api_model import BaseAPIModel
from any_api.openapi.model.openapi_model import TagModel
from any_api.util import by_pydantic

__all__ = ["BaseAPI"]

_ModelT = TypeVar("_ModelT", bound=BaseAPIModel)


class BaseAPI(Generic[_ModelT]):
    _api_model: _ModelT
    _schema_key: str = "schemas"
    _add_tag_dict: dict = {}

    def _add_tag(self, tag: TagModel) -> None:
        if tag.name not in self._add_tag_dict:
            self._add_tag_dict[tag.name] = tag.description
            self._api_model.tags.append(tag)
        elif tag.description != self._add_tag_dict[tag.name]:
            raise ValueError(
                f"tag:{tag.name} already exists, but the description of the tag is inconsistent with the current one"
            )

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

    def _schema_handle(self, model: Type[BaseModel], enable_move_to_component: bool = True) -> Tuple[str, dict]:
        global_model_name = by_pydantic.get_model_global_name(model)

        schema_dict: dict = copy.deepcopy(by_pydantic.any_api_model_schema(model))
        self._replace_pydantic_definitions(schema_dict)
        if "definitions" in schema_dict:
            # fix del schema dict
            del schema_dict["definitions"]
        if enable_move_to_component:
            self._api_model.components[self._schema_key].update({global_model_name: schema_dict})
        return global_model_name, schema_dict

    @property
    def model(self) -> _ModelT:
        return self._api_model

    @property
    def dict(self) -> dict:
        openapi_dict: dict = self._api_model.dict(exclude_none=True, by_alias=True)
        # if not openapi_dict["info"]["terms_of_service"]:
        #     del openapi_dict["info"]["terms_of_service"]
        #
        # if not openapi_dict["info"]["content"]:
        #     del openapi_dict["info"]["license"]
        return openapi_dict

    def content(self, type_: str = "json", **kwargs: Any) -> str:
        openapi_dict: dict = self.dict
        if type_ == "json":
            return json.dumps(openapi_dict, **kwargs)
        elif type_ == "yaml":
            try:
                import yaml  # type: ignore

                return yaml.dump(openapi_dict, **kwargs)
            except ImportError:
                raise RuntimeError("Please install yaml")
        else:
            raise ValueError(f"Not supoprt type:{type_}")
