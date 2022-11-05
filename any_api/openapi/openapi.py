import logging
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

import any_api.openapi.model.util
from any_api.base_api.base_api import BaseAPI
from any_api.openapi.model import openapi_model, request_model, response_model
from any_api.openapi.model.util import HttpMethodLiteral

__all__ = ["OpenAPI"]


class OpenAPI(BaseAPI[openapi_model.OpenAPIModel]):
    def __init__(
        self,
        openapi_info_model: Optional[openapi_model.InfoModel] = None,
        server_model_list: Optional[List[openapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[openapi_model.TagModel]] = None,
        external_docs: Optional[openapi_model.ExternalDocumentationModel] = None,
        security_dict: Optional[Dict[str, openapi_model.SecurityModelType]] = None
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
        if external_docs:
            self._api_model.external_docs = external_docs
        if security_dict:
            self._api_model.components["securitySchemes"] = security_dict
        if tag_model_list:
            for tag_model in tag_model_list:
                self._add_tag(tag_model)

    @classmethod
    def build(
        cls,
        openapi_info_model: Optional[openapi_model.InfoModel] = None,
        server_model_list: Optional[List[openapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[openapi_model.TagModel]] = None,
        external_docs: Optional[openapi_model.ExternalDocumentationModel] = None,
    ) -> "OpenAPI":
        return cls(
            openapi_info_model=openapi_info_model,
            server_model_list=server_model_list,
            tag_model_list=tag_model_list,
            external_docs=external_docs,
        )

    def _header_handle(self, model: BaseModel) -> Dict[str, openapi_model.HeaderModel]:
        header_dict: Dict[str, openapi_model.HeaderModel] = {}
        for key, value in model.schema()["properties"].items():
            header_dict[key] = openapi_model.HeaderModel(
                description=value.get("description", ""),
                required=key in model.schema().get("required", []),
                deprecated=value.get("deprecated", False),
                example=value.get("example", None),
                schema={
                    k: v
                    for k, v in value.items()
                    if k not in ("title", "description", "required", "deprecated", "example")
                },
            )
        return header_dict

    def _parameter_handle(
        self,
        param_type: str,
        operation_model: openapi_model.OperationModel,
        api_request_model: request_model.RequestModel,
    ) -> None:
        if isinstance(api_request_model.model, tuple):
            raise ValueError("parameter not support array model")
        _, schema_dict = self._schema_handle(api_request_model.model, enable_move_to_component=False)
        for key, property_dict in schema_dict["properties"].items():
            description: str = property_dict.get("description", "") or ""
            required: bool = key in schema_dict.get("required", [])
            if param_type == "cookie":
                description += (
                    " \n"
                    ">Note for Swagger UI and Swagger Editor users: "
                    " \n"
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
            operation_model.parameters.append(
                openapi_model.ParameterModel(
                    **{
                        "name": key,
                        "required": required,
                        "description": description,
                        "schema": {k: v for k, v in property_dict.items() if k not in ("title", "description")},
                        "in": param_type,
                    }
                )
            )

    def _body_handle(
        self,
        param_type: str,
        operation_model: openapi_model.OperationModel,
        api_request_model: request_model.RequestModel,
    ) -> None:
        """
        gen request body schema and update request body schemas'definitions to components schemas
        Doc: https://swagger.io/docs/specification/describing-request-body/
        """
        if operation_model.request_body is None:
            operation_model.request_body = openapi_model.RequestBodyModel(
                required=api_request_model.required,
                description=api_request_model.description or api_request_model.__doc__ or "",
            )

        request_body_is_array: bool = False
        if isinstance(api_request_model.model, tuple):
            request_body_model: Type[BaseModel] = api_request_model.model[0]
            request_body_is_array = True
        else:
            request_body_model = api_request_model.model
        global_model_name, schema_dict = self._schema_handle(
            request_body_model, enable_move_to_component=param_type != "multiform"
        )
        for media_type in api_request_model.media_type_list:
            content_dict: Dict[str, openapi_model.MediaTypeModel] = operation_model.request_body.content

            if param_type == "multiform":
                if media_type in content_dict:
                    for key, value in content_dict[media_type].schema_.items():
                        if isinstance(value, list):
                            value.extend(schema_dict[key])
                        elif isinstance(value, dict):
                            value.update(schema_dict[key])
                else:
                    content_dict[media_type] = openapi_model.MediaTypeModel(schema=schema_dict)
                for key, property_dict in schema_dict["properties"].items():
                    if not api_request_model.openapi_serialization:
                        raise ValueError(f"When param type is {param_type}, openapi serialization cannot be empty")
                    if content_dict[media_type].encoding is None:
                        content_dict[media_type].encoding = {}
                    content_dict[media_type].encoding[key] = openapi_model.EncodingModel(  # type: ignore
                        **api_request_model.openapi_serialization
                    )
                    if "multipart/form-data" in content_dict:
                        content_dict[media_type].schema_["properties"][key][
                            "description"
                        ] += "     \n >Swagger UI could not support, when media_type is multipart/form-data"
            else:
                if media_type in content_dict:
                    if request_body_is_array:
                        raise ValueError("request body is array, not support multi diff request body")
                    if "oneOf" not in content_dict[media_type].schema_:
                        content_dict[media_type].schema_["oneOf"] = []
                    exist_ref_key: str = content_dict[media_type].schema_.pop("$ref", "")
                    if exist_ref_key:
                        content_dict[media_type].schema_["oneOf"].append({"$ref": exist_ref_key})
                    content_dict[media_type].schema_["oneOf"].append(
                        {"$ref": f"#/components/schemas/{global_model_name}"}
                    )
                else:
                    if request_body_is_array:
                        content_dict[media_type] = openapi_model.MediaTypeModel(
                            schema={"type": "array", "items": {"$ref": f"#/components/schemas/{global_model_name}"}}
                        )
                    else:
                        content_dict[media_type] = openapi_model.MediaTypeModel(
                            schema={"$ref": f"#/components/schemas/{global_model_name}"}
                        )
            # TODO support payload?
            # https://swagger.io/docs/specification/describing-request-body/

    def _file_upload_handle(
        self,
        operation_model: openapi_model.OperationModel,
        api_request_model: request_model.RequestModel,
    ) -> None:
        """https://swagger.io/docs/specification/describing-request-body/file-upload/"""
        if isinstance(api_request_model.model, tuple):
            raise ValueError("file body not support array model")
        if operation_model.request_body is None:
            operation_model.request_body = openapi_model.RequestBodyModel()
        content_dict: Dict[str, openapi_model.MediaTypeModel] = operation_model.request_body.content
        schema_dict: dict = api_request_model.model.schema()
        for media_type in api_request_model.media_type_list:
            required_column_list: List[str] = schema_dict.get("required", [])
            properties_dict: dict = {
                param_name: {"title": property_dict["title"], "type": "string", "format": "binary"}
                for param_name, property_dict in schema_dict.get("properties", {}).items()
            }
            if media_type not in content_dict:
                set_schema_dict: dict = {
                    "type": "object",
                    "properties": properties_dict,
                }
                if required_column_list:
                    set_schema_dict["required"] = required_column_list
                content_dict[media_type] = openapi_model.MediaTypeModel(schema=set_schema_dict)
            else:
                content_dict[media_type].schema_["properties"].update(properties_dict)
                if required_column_list:
                    content_dict[media_type].schema_["required"].extend(required_column_list)

    def _request_handle(
        self,
        api_model: request_model.ApiModel,
        operation_model: openapi_model.OperationModel,
    ) -> None:
        for param_type in any_api.openapi.model.util.HttpParamTypeLiteral.__args__:  # type: ignore
            request_model_list = api_model.request_dict.get(param_type, [])
            if not request_model_list:
                continue
            for api_request_model in request_model_list:
                if param_type in ("cookie", "header", "path", "query"):
                    self._parameter_handle(param_type, operation_model, api_request_model)
                elif param_type in ("body", "form", "multiform"):
                    if not api_request_model.media_type_list:
                        raise ValueError(f"Can not found {param_type} `model's media_type`")
                    self._body_handle(param_type, operation_model, api_request_model)
                elif param_type in ("file",):
                    self._file_upload_handle(operation_model, api_request_model)

    def _response_handle(
        self,
        api_model: request_model.ApiModel,
        operation_model: openapi_model.OperationModel,
    ) -> None:
        response_schema_dict: Dict[tuple, List[Dict[str, str]]] = {}
        core_resp_model: Optional[response_model.BaseResponseModel] = None
        for resp_model_class in api_model.response_list:
            resp_model: response_model.BaseResponseModel = resp_model_class()
            if core_resp_model is None or core_resp_model.is_core:
                core_resp_model = resp_model

            global_model_name: str = ""
            if (
                getattr(resp_model, "response_data", None)
                and isinstance(resp_model.response_data, type)
                and issubclass(resp_model.response_data, BaseModel)
            ):
                global_model_name, schema_dict = self._schema_handle(resp_model.response_data)
                if resp_model.name is not None:
                    schema_dict["title"] = resp_model.name

            for _status_code in resp_model.status_code:
                status_code_str: str = str(_status_code)
                key: tuple = (status_code_str, resp_model.media_type)
                header_dict = self._header_handle(resp_model.header) if resp_model.header else {}
                if status_code_str in operation_model.responses:
                    if resp_model.description:
                        operation_model.responses[status_code_str].description += f"|{resp_model.description}"
                    if resp_model.header:
                        response_header_dict = operation_model.responses[status_code_str].headers or {}
                        response_header_dict.update(header_dict)
                        operation_model.responses[status_code_str].headers = response_header_dict
                else:
                    operation_model.responses[status_code_str] = openapi_model.ResponseModel(
                        description=resp_model.description or "", headers=header_dict
                    )

                if _status_code == 204:
                    # 204 No Content, have no body.
                    # To indicate the response body is empty, do not specify a content for the response
                    continue

                response: openapi_model.ResponseModel = operation_model.responses[status_code_str]

                if resp_model.links_model_dict:
                    response.links = resp_model.links_model_dict

                if global_model_name:
                    openapi_schema_dict: dict = {"$ref": f"#/components/schemas/{global_model_name}"}
                    if key in response_schema_dict:
                        response_schema_dict[key].append(openapi_schema_dict)
                    else:
                        response_schema_dict[key] = [openapi_schema_dict]
                elif resp_model.openapi_schema:
                    if response.content is None:
                        response.content = {}
                    if resp_model.media_type in response.content:
                        raise ValueError(
                            f"{resp_model.media_type} already exists, "
                            f"Please check {api_model.operation_id}'s "
                            f"response model list:{api_model.response_list}"
                        )
                    response.content[resp_model.media_type] = openapi_model.MediaTypeModel(
                        schema=resp_model.openapi_schema
                    )
                else:
                    logging.warning(
                        f"Can not found response schema from {api_model.operation_id}'s response model:{resp_model}"
                    )
        # mutli response support
        # only response example see https://swagger.io/docs/specification/describing-responses/   FAQ
        for key_tuple, path_list in response_schema_dict.items():
            status_code_str, media_type = key_tuple
            if len(path_list) == 1:
                openapi_schema_dict = path_list[0]
            else:
                openapi_schema_dict = {"oneOf": path_list}

            content_dict: Dict[str, openapi_model.MediaTypeModel] = (
                operation_model.responses[status_code_str].content or {}
            )
            content_dict[media_type] = openapi_model.MediaTypeModel(schema=openapi_schema_dict)
            operation_model.responses[status_code_str].content = content_dict

    def add_api_model(self, api_model: request_model.ApiModel) -> "OpenAPI":
        path_dict: Dict[HttpMethodLiteral, openapi_model.OperationModel] = {}
        if api_model.path not in self._api_model.paths:
            self._api_model.paths[api_model.path] = path_dict
        else:
            path_dict = self._api_model.paths[api_model.path]

        for http_method in api_model.http_method_list:
            if http_method in path_dict:
                raise ValueError(f"{http_method} already exists in {api_model.path}")

            operation_model: openapi_model.OperationModel = openapi_model.OperationModel(
                operationId=api_model.operation_id,
                deprecated=api_model.deprecated,
                description=api_model.description,
                summary=api_model.summary,
                security=api_model.security,
            )
            if api_model.tags:
                for tag in api_model.tags:
                    self._add_tag(tag)
                operation_model.tags = [i.name for i in api_model.tags]
            # TODO check security

            api_model.add_to_operation_model(operation_model)

            if api_model.request_dict:
                self._request_handle(api_model, operation_model)
            if api_model.response_list:
                self._response_handle(api_model, operation_model)
            path_dict[http_method] = operation_model
        return self
