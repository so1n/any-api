import copy
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from any_api.openapi.model import openapi_model, request_model, response_model
from any_api.util import by_pydantic

__all__ = ["OpenAPI"]


class OpenAPI(object):
    def __init__(
        self,
        openapi_info_model: Optional[openapi_model.OpenApiInfoModel] = None,
        server_model_list: Optional[List[openapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[openapi_model.TagModel]] = None,
        # default_response: Optional[...] = None,  # TODO
    ):
        self._header_keyword_dict: Dict[str, str] = {
            "Content-Type": "requestBody.content.<media-type>",
            "Accept": "responses.<code>.content.<media-type>",
            "Authorization": " security",
        }
        self._add_tag_dict: dict = {}

        self._api_model: openapi_model.OpenAPIModel = openapi_model.OpenAPIModel()
        if openapi_info_model:
            self._api_model.info = openapi_info_model
        if server_model_list:
            self._api_model.servers = server_model_list
        if tag_model_list:
            for tag_model in tag_model_list:
                self._add_tag(tag_model)

    @classmethod
    def build(
        cls,
        openapi_info_model: Optional[openapi_model.OpenApiInfoModel] = None,
        server_model_list: Optional[List[openapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[openapi_model.TagModel]] = None,
    ) -> "OpenAPI":
        return cls(
            openapi_info_model=openapi_info_model, server_model_list=server_model_list, tag_model_list=tag_model_list
        )

    def _add_tag(self, tag: openapi_model.TagModel) -> None:
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
                schema[key] = f"#/components/schemas/{model_key}"
                self._api_model.components["schemas"][model_key] = parent_schema["definitions"][model_key]
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
            self._api_model.components["schemas"].update({global_model_name: schema_dict})
        return global_model_name, schema_dict

    def _parameter_handle(
        self,
        param_type: str,
        openapi_method_dict: dict,
        invoke_request_model: request_model.RequestModel,
    ) -> None:
        _, schema_dict = self._schema_handle(invoke_request_model.model, enable_move_to_component=False)
        openapi_parameters_list: list = openapi_method_dict.setdefault("parameters", [])
        for key, property_dict in schema_dict["properties"].items():
            description: str = property_dict.get("description", "") or ""
            required: bool = key in property_dict.get("required", [])
            if param_type == "cookie":
                description += (
                    " "
                    "\n"
                    ">Note for Swagger UI and Swagger Editor users: "
                    " "
                    "\n"
                    ">Cookie authentication is"
                    'currently not supported for "try it out" requests due to browser security'
                    "restrictions. "
                    "See [this issue](https://github.com/swagger-api/swagger-js/issues/1163)"
                    "for more information. "
                    "[SwaggerHub](https://swagger.io/tools/swaggerhub/)"
                    "does not have this limitation. "
                )
            elif param_type == "path" and not required:
                raise ValueError("That path parameters must have required: true, because they are always required")
            openapi_parameters_list.append(
                {
                    "name": key,
                    "in": param_type,
                    "required": required,
                    "description": description,
                    "schema": {k: v for k, v in property_dict.items() if k not in ("title", "description")},
                }
            )

    def _body_handle(
        self,
        param_type: str,
        openapi_method_dict: dict,
        invoke_request_model: request_model.RequestModel,
    ) -> None:
        """
        gen request body schema and update request body schemas'definitions to components schemas
        Doc: https://swagger.io/docs/specification/describing-request-body/
        """
        openapi_request_body_dict: dict = openapi_method_dict.setdefault("requestBody", {"content": {}})
        global_model_name, schema_dict = self._schema_handle(
            invoke_request_model.model, enable_move_to_component=param_type != "multiform"
        )
        media_type: str = invoke_request_model.media_type

        if param_type == "multiform":
            if media_type in openapi_request_body_dict["content"]:
                for key, value in openapi_request_body_dict["content"][media_type]["schema"].items():
                    if isinstance(value, list):
                        value.extend(schema_dict[key])
                    elif isinstance(value, dict):
                        value.update(schema_dict[key])
            else:
                openapi_request_body_dict["content"][media_type] = {"schema": schema_dict}
            form_encoding_dict = openapi_request_body_dict["content"][media_type].setdefault("encoding", {})
            for key, property_dict in schema_dict["properties"].items():
                if not invoke_request_model.openapi_serialization:
                    raise ValueError(f"When param type is {param_type}, openapi serialization cannot be empty")
                form_encoding_dict[key] = invoke_request_model.openapi_serialization
                if "multipart/form-data" in openapi_request_body_dict["content"]:
                    openapi_request_body_dict["content"][media_type]["schema"]["properties"][key][
                        "description"
                    ] += "     \n >Swagger UI could not support, when media_type is multipart/form-data"
        else:
            if media_type in openapi_request_body_dict["content"]:
                if "oneOf" not in openapi_request_body_dict["content"][media_type]["schema"]:
                    openapi_request_body_dict["content"][media_type]["schema"]["oneOf"] = []
                exist_ref_key: str = openapi_request_body_dict["content"][media_type]["schema"].pop("$ref", "")
                if exist_ref_key:
                    openapi_request_body_dict["content"][media_type]["schema"]["oneOf"].append({"$ref": exist_ref_key})
                openapi_request_body_dict["content"][media_type]["schema"]["oneOf"].append(
                    {"$ref": f"#/components/schemas/{global_model_name}"}
                )
            else:
                openapi_request_body_dict["content"][media_type] = {
                    "schema": {"$ref": f"#/components/schemas/{global_model_name}"}
                }
        # TODO support payload?
        # https://swagger.io/docs/specification/describing-request-body/

    def _file_upload_handle(
        self,
        openapi_method_dict: dict,
        invoke_request_model: request_model.RequestModel,
    ) -> None:
        """https://swagger.io/docs/specification/describing-request-body/file-upload/"""
        openapi_request_body_dict: dict = openapi_method_dict.setdefault("requestBody", {"content": {}})
        schema_dict: dict = invoke_request_model.model.schema()
        media_type: str = invoke_request_model.media_type
        required_column_list: List[str] = schema_dict.get("required", [])
        properties_dict: dict = {
            param_name: {"title": property_dict["title"], "type": "string", "format": "binary"}
            for param_name, property_dict in schema_dict.get("properties", {}).items()
        }
        if invoke_request_model.media_type not in openapi_request_body_dict["content"]:
            set_schema_dict: dict = {
                "type": "object",
                "properties": properties_dict,
            }
            if required_column_list:
                set_schema_dict["required"] = required_column_list
            openapi_request_body_dict["content"][media_type] = {"schema": set_schema_dict}
        else:
            openapi_request_body_dict["content"][media_type]["schema"]["properties"].update(properties_dict)
            if required_column_list:
                openapi_request_body_dict["content"][media_type]["schema"]["required"].extend(required_column_list)

    def _input_handle(
        self,
        invoke_model: request_model.InvokeModel,
        openapi_method_dict: dict,
    ) -> None:
        for param_type in request_model.HttpParamTypeLiteral.__args__:  # type: ignore
            request_model_list = invoke_model.input_dict.get(param_type, [])
            if not request_model_list:
                continue
            for invoke_request_model in request_model_list:
                if param_type in ("cookie", "header", "path", "query"):
                    self._parameter_handle(param_type, openapi_method_dict, invoke_request_model)
                elif param_type in ("body", "form", "multiform"):
                    if not invoke_request_model.media_type:
                        raise ValueError(f"Can not found {param_type} `model's media_type`")
                    self._body_handle(param_type, openapi_method_dict, invoke_request_model)
                elif param_type in ("file",):
                    self._file_upload_handle(openapi_method_dict, invoke_request_model)

    def _output_handle(
        self,
        invoke_model: request_model.InvokeModel,
        openapi_method_dict: dict,
    ) -> None:
        openapi_response_dict: dict = openapi_method_dict.setdefault("responses", {})
        response_schema_dict: Dict[tuple, List[Dict[str, str]]] = {}
        for resp_model_class in invoke_model.output_list:
            resp_model: response_model.BaseResponseModel = resp_model_class()
            global_model_name: str = ""
            if (
                getattr(resp_model, "response_data", None)
                and isinstance(resp_model.response_data, type)
                and issubclass(resp_model.response_data, BaseModel)
            ):
                global_model_name, schema_dict = self._schema_handle(resp_model.response_data)
            for _status_code in resp_model.status_code:
                key: tuple = (_status_code, resp_model.media_type)
                if _status_code in openapi_response_dict:
                    if resp_model.description:
                        openapi_response_dict[_status_code]["description"] += f"|{resp_model.description}"
                    if resp_model.header:
                        openapi_response_dict[_status_code]["headers"].update(resp_model.header)
                else:
                    openapi_response_dict[_status_code] = {
                        "description": resp_model.description or "",
                        "headers": resp_model.header,
                    }
                if _status_code == 204:
                    # 204 No Content, have no body.
                    # To indicate the response body is empty, do not specify a content for the response
                    continue

                openapi_response_dict[_status_code]["content"] = {}
                if resp_model.links_schema_dict:
                    openapi_response_dict[_status_code]["links"] = resp_model.links_schema_dict

                if global_model_name:
                    openapi_schema_dict: dict = {"$ref": f"#/components/schemas/{global_model_name}"}
                    if key in response_schema_dict:
                        response_schema_dict[key].append(openapi_schema_dict)
                    else:
                        response_schema_dict[key] = [openapi_schema_dict]
                elif resp_model.openapi_schema:
                    if resp_model.media_type in openapi_response_dict[_status_code]["content"]:
                        raise ValueError(
                            f"{resp_model.media_type} already exists, "
                            f"Please check {invoke_model.operation_id}'s "
                            f"response model list:{invoke_model.output_list}"
                        )
                    openapi_response_dict[_status_code]["content"][resp_model.media_type] = resp_model.openapi_schema
                else:
                    logging.warning(
                        f"Can not found response schema from {invoke_model.operation_id}'s response model:{resp_model}"
                    )
        # mutli response support
        # only response example see https://swagger.io/docs/specification/describing-responses/   FAQ
        for key_tuple, path_list in response_schema_dict.items():
            status_code, media_type = key_tuple
            if len(path_list) == 1:
                openapi_schema_dict = path_list[0]
            else:
                openapi_schema_dict = {"oneOf": path_list}
            openapi_response_dict[status_code]["content"] = {media_type: {"schema": openapi_schema_dict}}

    @property
    def model(self) -> openapi_model.OpenAPIModel:
        return self._api_model

    @property
    def dict(self) -> dict:
        openapi_dict: dict = self._api_model.dict(exclude_none=True)
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

    def add_invoke_model(self, invoke_model: request_model.InvokeModel) -> "OpenAPI":
        openapi_path_dict: dict = self._api_model.paths.setdefault(invoke_model.path, {})
        for http_method in invoke_model.http_method_list:
            openapi_method_dict: dict = openapi_path_dict.setdefault(http_method.lower(), {})
            if invoke_model.tags:
                for tag in invoke_model.tags:
                    self._add_tag(tag)
                openapi_method_dict["tags"] = [tag.name for tag in invoke_model.tags]
            openapi_method_dict["operationId"] = f"{http_method}.{invoke_model.operation_id}"
            openapi_method_dict["deprecated"] = invoke_model.deprecated
            openapi_method_dict["description"] = invoke_model.description
            openapi_method_dict["summary"] = invoke_model.summary
            invoke_model.add_to_openapi_method_dict(openapi_method_dict)
            if invoke_model.input_dict:
                self._input_handle(invoke_model, openapi_method_dict)
            if invoke_model.output_list:
                self._output_handle(invoke_model, openapi_method_dict)
        return self
