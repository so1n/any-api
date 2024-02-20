from typing import Dict, List, Optional, Set, Type

from pydantic import BaseModel
from typing_extensions import Literal

from any_api.base_api.base_api import BaseAPI
from any_api.openapi.model import ApiModel
from any_api.openapi.model import openapi as openapi_model
from any_api.openapi.model import requests, responses
from any_api.openapi.model.util import HttpMethodLiteral, HttpParamTypeLiteral
from any_api.util import pydantic_adapter

__all__ = ["OpenAPI"]


def get_response_list(resp_model: responses.BaseOpenAPIResponseModel) -> List[responses.BaseResponseModel]:
    resp_model_list: List[responses.BaseResponseModel] = []
    resp_model_class_list: List[responses.UnionResponseType] = []
    if isinstance(resp_model, responses.UnionResponseModel):
        resp_model_class_list = resp_model.response_list or []
    elif isinstance(resp_model, responses.BaseResponseModel):
        resp_model_list.append(resp_model)
    else:
        raise TypeError("response list only support UnionResponseModel or BaseResponseModel")
    for resp_model_class in resp_model_class_list:
        resp_model_list.append(resp_model_class())
    return resp_model_list


class OpenAPI(BaseAPI[openapi_model.OpenAPIModel, ApiModel]):
    def __init__(
        self,
        openapi_version: str = "3.0.0",
        openapi_info_model: Optional[openapi_model.InfoModel] = None,
        server_model_list: Optional[List[openapi_model.ServerModel]] = None,
        tag_model_list: Optional[List[openapi_model.TagModel]] = None,
        external_docs: Optional[openapi_model.ExternalDocumentationModel] = None,
        security_dict: Optional[Dict[str, openapi_model.SecurityModelType]] = None,
        # default_response: Optional[...] = None,  # TODO
        # If you want to know why, check it out `pydantic_adapter.remove_any_of` func __doc__
        enable_remove_any_of: bool = not pydantic_adapter.is_v1,
        swagger_doc_add_not_support_annotation: bool = True,
    ):
        super().__init__()

        self._enable_remove_any_of = enable_remove_any_of
        self._swagger_doc_add_not_support_annotation = swagger_doc_add_not_support_annotation
        self._header_keyword_dict: Dict[str, str] = {
            "Content-Type": "requestBody.content.<media-type>",
            "Accept": "responses.<code>.content.<media-type>",
            "Authorization": " security",
        }
        self._api_model: openapi_model.OpenAPIModel = openapi_model.OpenAPIModel(openapi=openapi_version)

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

    def _header_handle(self, model: Type[BaseModel]) -> Dict[str, openapi_model.HeaderModel]:
        """Generate a HeaderModel dict from BaseModel's Field"""
        header_dict: Dict[str, openapi_model.HeaderModel] = {}
        model_schema: dict = pydantic_adapter.model_json_schema(model)
        for key, value in model_schema["properties"].items():
            header_dict[key] = openapi_model.HeaderModel(
                description=value.get("description", ""),
                required=key in model_schema.get("required", []),
                deprecated=value.get("deprecated", False),
                example=value.get("example", None),
                examples=value.get("examples", None),
                explode=value.get("explode", False),
                schema={
                    k: v
                    for k, v in value.items()
                    if k not in ("title", "description", "required", "deprecated", "example", "examples", "explode")
                },
            )
        return header_dict

    def _parameter_handle(
        self,
        *,
        api_model: ApiModel,
        operation_model: openapi_model.OperationModel,
        api_request: requests.RequestModel,
        param_type: Literal["query", "header", "path", "cookie"],
    ) -> None:
        if isinstance(api_request.model, tuple):
            raise ValueError("parameter not support array model")
        global_model_name, schema_dict = self._get_in_components_model_schema(api_request.model)
        self._model_use_count[api_request.model] -= 1
        if self._model_use_count[api_request.model] == 0:
            del self._definitions[global_model_name]

        for key, property_dict in schema_dict["properties"].items():
            description: str = property_dict.get("description", "") or ""
            required: bool = key in schema_dict.get("required", [])
            if param_type == "cookie" and self._swagger_doc_add_not_support_annotation:
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
            parameters = operation_model.parameters or []
            parameters.append(
                openapi_model.ParameterModel(
                    name=key,
                    required=required,
                    deprecated=property_dict.get("deprecated", False),
                    description=description,
                    schema={
                        k: v
                        for k, v in property_dict.items()
                        if k not in ("title", "description", "explode", "example", "examples", "deprecated")
                    },
                    in_stub=param_type,
                    explode=property_dict.get("explode", False),
                    example=property_dict.get("example", None),
                    examples=property_dict.get("examples", None),
                )
            )
            operation_model.parameters = parameters

    def _body_handle(
        self,
        *,
        api_model: ApiModel,
        operation_model: openapi_model.OperationModel,
        api_request: requests.RequestModel,
        param_type: str,
    ) -> None:
        """
        gen request body schema and update request body schemas'definitions to components schemas
        Doc: https://swagger.io/docs/specification/describing-request-body/
        """
        request_body_is_array: bool = False
        if isinstance(api_request.model, tuple):
            request_body_model: Type[BaseModel] = api_request.model[0]
            request_body_is_array = True
        else:
            request_body_model = api_request.model

        if operation_model.request_body is None:
            operation_model.request_body = openapi_model.RequestBodyModel(
                required=api_request.required,
                description=api_request.description or api_request.__doc__ or "",
            )

        for media_type in api_request.media_type_list:
            content_dict: Dict[str, openapi_model.MediaTypeModel] = operation_model.request_body.content
            if param_type == "multiform":
                # Limit the ability to parse data from only one HTTP method
                multiform_model_set: Set[Type[BaseModel]] = getattr(request_body_model, "multiform_model_set", set())
                if request_body_model in multiform_model_set:
                    continue
                multiform_model_set.add(request_body_model)
                setattr(request_body_model, "multiform_model_set", multiform_model_set)
                # multiform not save to components
                schema_dict = self._get_not_in_components_model_schema(request_body_model)
                if media_type in content_dict:
                    for key, value in self._get_real_schema_dict(content_dict[media_type].schema_).items():
                        if isinstance(value, list):
                            value.extend(schema_dict[key])
                        elif isinstance(value, dict):
                            value.update(schema_dict[key])
                else:
                    content_dict[media_type] = openapi_model.MediaTypeModel(schema=schema_dict)

                if not api_request.openapi_serialization:
                    raise ValueError(f"When param type is {param_type}, openapi serialization cannot be empty")
                for key, property_dict in schema_dict["properties"].items():
                    if content_dict[media_type].encoding is None:
                        content_dict[media_type].encoding = {}
                    content_dict[media_type].encoding[key] = api_request.openapi_serialization  # type: ignore[index]
                    if "multipart/form-data" in content_dict and self._swagger_doc_add_not_support_annotation:
                        self._get_real_schema_dict(content_dict[media_type].schema_)["properties"][key][
                            "description"
                        ] += "     \n >Swagger UI could not support, when media_type is multipart/form-data"
            else:
                global_model_name, schema_dict = self._get_in_components_model_schema(request_body_model)
                if "application/xml" == media_type:
                    self._xml_handler(schema_dict)

                if api_request.nested_model_key is not None:
                    real_schema_dict = schema_dict["properties"][api_request.nested_model_key]
                else:
                    real_schema_dict = {"$ref": f"#/components/schemas/{global_model_name}"}

                if media_type in content_dict:
                    if request_body_is_array:
                        raise ValueError("request body is array, not support multi diff request body")
                    if "oneOf" not in content_dict[media_type].schema_:
                        content_dict[media_type].schema_["oneOf"] = []
                    exist_ref_key: str = content_dict[media_type].schema_.pop("$ref", "")
                    if exist_ref_key:
                        content_dict[media_type].schema_["oneOf"].append({"$ref": exist_ref_key})
                    content_dict[media_type].schema_["oneOf"].append(real_schema_dict)
                else:
                    if request_body_is_array:
                        real_schema_dict = {"type": "array", "items": real_schema_dict}
                    content_dict[media_type] = openapi_model.MediaTypeModel(schema=real_schema_dict)
            # TODO support payload?
            # https://swagger.io/docs/specification/describing-request-body/

    def _file_upload_handle(
        self,
        *,
        api_model: ApiModel,
        operation_model: openapi_model.OperationModel,
        api_request: requests.RequestModel,
        param_type: str,
    ) -> None:
        """https://swagger.io/docs/specification/describing-request-body/file-upload/"""
        if operation_model.request_body is None:
            operation_model.request_body = openapi_model.RequestBodyModel(
                required=api_request.required,
                description=api_request.description or api_request.__doc__ or "",
            )

        content_dict: Dict[str, openapi_model.MediaTypeModel] = operation_model.request_body.content

        if isinstance(api_request.model, tuple):
            request_model_list: List[Type[BaseModel]] = list(api_request.model)
        else:
            request_model_list = [api_request.model]

        for request_model in request_model_list:
            schema_dict: dict = pydantic_adapter.model_json_schema(request_model)
            for media_type in api_request.media_type_list:
                required_column_list: List[str] = schema_dict.get("required", [])
                properties_dict: dict = {}
                for param_name, property_dict in schema_dict.get("properties", {}).items():
                    properties_dict[param_name] = {
                        "title": property_dict["title"],
                        "type": property_dict.get("type", "string"),
                    }
                    if "type" not in property_dict and "format" not in property_dict:
                        properties_dict[param_name]["format"] = "binary"

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
        api_model: ApiModel,
        operation_model: openapi_model.OperationModel,
    ) -> None:
        for param_type in HttpParamTypeLiteral.__args__:  # type: ignore
            request_model_list = api_model.request_dict.get(param_type, [])
            if not request_model_list:
                continue
            for api_request_model in request_model_list:
                if param_type in ("cookie", "header", "path", "query"):
                    self._parameter_handle(
                        api_model=api_model,
                        operation_model=operation_model,
                        api_request=api_request_model,
                        param_type=param_type,
                    )
                elif param_type in ("body", "form", "json", "multiform"):
                    if not api_request_model.media_type_list:
                        raise ValueError(f"Can not found {param_type} `model's media_type`")
                    self._body_handle(
                        api_model=api_model,
                        operation_model=operation_model,
                        api_request=api_request_model,
                        param_type=param_type,
                    )
                elif param_type in ("file",):
                    if isinstance(api_request_model.model, tuple):
                        raise ValueError("file body not support array model")
                    self._file_upload_handle(
                        api_model=api_model,
                        operation_model=operation_model,
                        api_request=api_request_model,
                        param_type=param_type,
                    )

    # flake8: noqa: C901
    def _response_handle(
        self,
        api_model: ApiModel,
        operation_model: openapi_model.OperationModel,
    ) -> None:
        response_schema_dict: Dict[tuple, List[dict]] = {}
        response_dict = operation_model.responses

        for resp_model_class in api_model.response_list:
            check_msg: str = f"Please check {api_model.operation_id}'s response model list:{api_model.response_list}"
            resp_model: responses.BaseOpenAPIResponseModel = resp_model_class()

            if isinstance(resp_model.status_code, str):
                # support status_code is default
                status_code_tuple: tuple = (resp_model.status_code,)
            else:
                status_code_tuple = resp_model.status_code

            for _status_code in status_code_tuple:
                status_code_str: str = str(_status_code)

                # init response and header handler
                header_dict = self._header_handle(resp_model.header) if resp_model.header else {}
                if status_code_str in response_dict:
                    if resp_model.description != resp_model.description:
                        raise ValueError(f"Response description already exits, {check_msg}")
                    if resp_model.header:
                        response_header_dict = response_dict[status_code_str].headers or {}
                        for header_key, header_value in header_dict.items():
                            if header_key not in response_header_dict:
                                response_header_dict[header_key] = header_value
                            elif response_header_dict[header_key] != header_value:
                                raise ValueError(f"Header Key:{header_key} already exits, {check_msg}")
                        response_dict[status_code_str].headers = response_header_dict or None
                else:
                    response_dict[status_code_str] = openapi_model.ResponseModel(
                        description=resp_model.description or "", headers=header_dict or None
                    )

                if _status_code == 204:
                    # 204 No Content, no body.
                    # To indicate the response body is empty, do not specify a content for the response
                    continue

                response: openapi_model.ResponseModel = response_dict[status_code_str]
                for real_resp_model in get_response_list(resp_model):
                    # link handler
                    if real_resp_model.links_model_dict:
                        link_dict = response.links or {}
                        for link_key, link_value in real_resp_model.links_model_dict.items():
                            if link_key in link_dict:
                                raise ValueError(f"Link Key:{link_key} already exits, {check_msg}")
                            link_dict[link_key] = link_value
                        response.links = link_dict

                    # schema handler
                    if real_resp_model.openapi_schema:
                        if response.content is None:
                            response.content = {}
                        if real_resp_model.media_type in response.content:
                            raise ValueError(f"Media type: {real_resp_model.media_type} already exists, {check_msg}")
                        response.content[real_resp_model.media_type] = openapi_model.MediaTypeModel(
                            schema=real_resp_model.openapi_schema
                        )
                    else:
                        global_model_name: str = ""
                        schema_dict: dict = {}
                        response_data_model = real_resp_model.get_response_data_model()
                        if response_data_model:
                            global_model_name, schema_dict = self._get_in_components_model_schema(response_data_model)
                            if "application/xml" == real_resp_model.media_type:
                                self._xml_handler(schema_dict)
                        if global_model_name or schema_dict:
                            if global_model_name:
                                openapi_schema_dict: dict = {"$ref": f"#/components/schemas/{global_model_name}"}
                            else:
                                openapi_schema_dict = schema_dict

                            key: tuple = (status_code_str, real_resp_model.media_type)
                            if real_resp_model.schema_type == "array":
                                openapi_schema_dict = {"type": "array", "items": openapi_schema_dict}
                                if "application/xml" == real_resp_model.media_type:
                                    openapi_schema_dict["xml"] = real_resp_model.__class__.__name__
                            if key in response_schema_dict:
                                response_schema_dict[key].append(openapi_schema_dict)
                            else:
                                response_schema_dict[key] = [openapi_schema_dict]
        # mutli response support
        # only response example see https://swagger.io/docs/specification/describing-responses/   FAQ
        for key_tuple, path_list in response_schema_dict.items():
            status_code_str, media_type = key_tuple
            content_dict: Dict[str, openapi_model.MediaTypeModel] = response_dict[status_code_str].content or {}
            if path_list:
                if len(path_list) == 1:
                    openapi_schema_dict = path_list[0]
                else:
                    openapi_schema_dict = {"oneOf": path_list}

                content_dict[media_type] = openapi_model.MediaTypeModel(schema=openapi_schema_dict)
            response_dict[status_code_str].content = content_dict
        operation_model.responses = response_dict

    def _load_definitions_by_api_model(self) -> None:
        in_components_model_list: List[Type[BaseModel]] = []
        model_use_count: Dict[Type[BaseModel], int] = {}

        def _add_model(model: Type[BaseModel], cnt: int = 1) -> None:
            in_components_model_list.append(model)
            if model not in model_use_count:
                model_use_count[model] = cnt
            else:
                model_use_count[model] += cnt

        for api_model in self._temp_model_list:
            for param_type in HttpParamTypeLiteral.__args__:  # type: ignore
                if param_type in ("multiform",):
                    # multiform model not load to components
                    continue
                request_model_list = api_model.request_dict.get(param_type, [])
                if not request_model_list:
                    continue
                for api_request_model in request_model_list:
                    if isinstance(api_request_model.model, tuple):
                        for _model in api_request_model.model:
                            _add_model(_model, cnt=len(api_model.http_method_list))
                    else:
                        _add_model(api_request_model.model, cnt=len(api_model.http_method_list))
            for resp_model_class in api_model.response_list:
                resp_model: responses.BaseOpenAPIResponseModel = resp_model_class()
                for real_resp_model in get_response_list(resp_model):
                    response_data_model = real_resp_model.get_response_data_model()
                    if response_data_model:
                        _add_model(response_data_model)

        self._model_name_map, self._definitions = pydantic_adapter.get_model_definitions(*in_components_model_list)
        if self._enable_remove_any_of:
            for k, v in self._definitions.items():
                pydantic_adapter.remove_any_of(v)
        self._api_model.components[self._schema_key] = self._definitions
        self._model_use_count = model_use_count

    def _add_request_to_api_model(self, api_model: ApiModel) -> "OpenAPI":
        path_dict: Dict[HttpMethodLiteral, openapi_model.OperationModel] = {}
        if api_model.path not in self._api_model.paths:
            self._api_model.paths[api_model.path] = path_dict
        else:
            path_dict = self._api_model.paths[api_model.path]

        for http_method in api_model.http_method_list:
            if http_method in path_dict:
                raise ValueError(f"{http_method} already exists in {api_model.path}")
            operation_model: openapi_model.OperationModel = openapi_model.OperationModel(
                operationId=(
                    f"{api_model.operation_id}_{http_method}"
                    if len(api_model.http_method_list) > 1
                    else api_model.operation_id
                ),
                deprecated=api_model.deprecated,
                description=api_model.description,
                summary=api_model.summary,
                tags=[i.name for i in api_model.tags],
            )
            if api_model.tags:
                self._add_tag(*api_model.tags)
            if api_model.security:
                self._add_security(api_model.security)
                operation_model.security = [{k: v.get_security_scope()} for k, v in (api_model.security or {}).items()]

            api_model.add_to_operation_model(operation_model)

            if api_model.request_dict:
                self._request_handle(api_model, operation_model)
            if api_model.response_list:
                self._response_handle(api_model, operation_model)
            path_dict[http_method] = operation_model
        return self
