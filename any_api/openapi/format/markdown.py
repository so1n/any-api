import json
from typing import Dict, List, Type, Union

from typing_extensions import TypedDict

from any_api.openapi.model import openapi_model
from any_api.openapi.openapi import OpenAPI
from any_api.util.i18n import I18n, I18nContext, i18n_local, join_i18n


class ParamTypedDict(TypedDict):
    name: str
    required: bool
    description: str
    example: str
    type: str
    other: dict


class Markdown(object):
    def __init__(
        self,
        openapi: OpenAPI,
        i18n_lang: str = i18n_local,
        i18n_class: Type[I18n] = I18n,
    ):
        self._openapi: OpenAPI = openapi
        self._i18n_lang: str = i18n_lang
        self._i18n_class: Type[I18n] = i18n_class

    @property
    def content(self) -> str:
        if self._i18n_lang == i18n_local:
            return self.gen_markdown_text()
        else:
            with I18nContext(self._i18n_lang):
                return self.gen_markdown_text()

    @staticmethod
    def _gen_md_table(result: List[dict], ident: int = 0) -> str:
        if not result:
            return ""
        md_text = f"{ident * ' '} |" + "|".join(result[0].keys()) + "|\n"
        md_text += f"{ident * ' '} |" + "|".join("---" for _ in result[0].keys()) + "|\n"
        for item in result:
            md_text += f"{ident * ' '} |" + "|".join([str(i) for i in item.values()]) + "|\n"
        return md_text

    def get_schema_dict(self, schema_obj: Union[openapi_model.RefModel, dict]) -> dict:
        if isinstance(schema_obj, openapi_model.RefModel):
            key_list: List[str] = schema_obj.ref[2:].split("/")
        elif isinstance(schema_obj, dict) and "$ref" in schema_obj:
            key_list = schema_obj["$ref"][2:].split("/")
        else:
            key_list = []

        if key_list:
            schema: dict = self._openapi.model.components
            for key in key_list[1:]:  # first item is components
                schema = schema[key]
        else:
            schema = schema_obj
        assert isinstance(schema, dict)
        return schema

    def request_body_handle(
        self,
        schema_obj: Union[openapi_model.RefModel, dict],
        nested: int = 0,
    ) -> List[dict]:
        parameter_list: List[dict] = []
        schema = self.get_schema_dict(schema_obj)
        if "oneOf" in schema:
            parameter_list.extend(self.request_body_handle(schema["oneOf"][0]))
            return parameter_list
        for name, property_dict in schema["properties"].items():
            if "$ref" in property_dict:
                parameter_list.extend(self.request_body_handle(property_dict, nested + 1))
            else:
                name_prefix: str = nested * " "
                if name_prefix:
                    name_prefix += "- "
                if "allOf" in property_dict:
                    property_dict = self.get_schema_dict(property_dict["allOf"][0])
                parameter_list.append(
                    {
                        I18n.Name: name_prefix + property_dict["title"],
                        I18n.Required: f"`{I18n.Required}`"
                        if property_dict["title"] in schema.get("required", [])
                        else "",
                        I18n.Type: property_dict["type"],
                        I18n.Desc: property_dict.get("description", ""),
                        I18n.Example: property_dict.get("example", ""),
                        I18n.Other: json.dumps(
                            {
                                k: v
                                for k, v in property_dict.items()
                                if k not in ("title", "description", "example", "type")
                            }
                        ),
                    }
                )
        return parameter_list

    def gen_head_info(self, http_method: str, path: str, operation_model: openapi_model.OperationModel) -> str:
        md_text: str = ""
        if operation_model.summary:
            md_text += f"**{I18n.Summary}**: {operation_model.summary}\n"
        if operation_model.description:
            md_text += f"    {operation_model.description}\n"
        if operation_model.tags:
            md_text += f"**{I18n.Tag}**: {', '.join([t.name for t in operation_model.tags])}"
        return md_text

    def gen_request_info(self, http_method: str, path: str, operation_model: openapi_model.OperationModel) -> str:
        md_text: str = ""
        md_text += f"- {I18n.Path}: {path}\n"
        md_text += f"- {I18n.Method}: {http_method}\n"
        md_text += f"- {I18n.Request}:\n"
        # parameter handle
        parameter_list: List[openapi_model.ParameterModel] = operation_model.parameters
        parameter_list.sort(key=lambda x: x.in_)
        parameter_dict: Dict[str, List[dict]] = {}
        for parameter in parameter_list:
            if parameter.in_ not in parameter_dict:
                parameter_dict[parameter.in_] = []

            schema = self.get_schema_dict(parameter.schema_)
            parameter_dict[parameter.in_].append(
                {
                    I18n.Name: parameter.name,
                    I18n.Required: f"`{I18n.Required}`" if parameter.required else "",
                    I18n.Type: schema["type"],
                    I18n.Desc: parameter.description,
                    I18n.Example: parameter.example or "",
                    I18n.Other: "",
                }
            )
        if operation_model.request_body:
            # body handle
            for content_type, media_model in operation_model.request_body.content.items():
                if content_type not in parameter_dict:
                    parameter_dict[content_type] = []
                parameter_dict[content_type].extend(self.request_body_handle(media_model.schema_))
        for _param_name, _parameter_list in parameter_dict.items():
            md_text += f"    *{_param_name}*\n\n"
            md_text += self._gen_md_table(_parameter_list, ident=4)

        return md_text

    def gen_response_info(self, http_method: str, path: str, operation_model: openapi_model.OperationModel) -> str:
        md_text: str = ""
        md_text += f"- {I18n.Response}\n"
        for status_code, response_model in operation_model.responses.items():
            md_text += f"*{I18n.Desc}*\n"
            md_text += response_model.description + "\n"
            if response_model.headers:
                md_text += "*Header*\n\n"
                self._gen_md_table([{"key": key, "value": value} for key, value in response_model.headers.items()])
            for content_type, media_type_model in response_model.content.items():
                md_text += f"    - {status_code}:{content_type}\n"
                md_text += f"    *{join_i18n([I18n.Response, I18n.Info])}*\n\n"
                md_text += self._gen_md_table(self.request_body_handle(media_type_model.schema_), ident=4)
                if media_type_model.example:
                    md_text += f"```json\n{media_type_model.example}\n```"
        return md_text

    def gen_tail_info(self, http_method: str, path: str, operation_model: openapi_model.OperationModel) -> str:
        return ""

    def gen_markdown_text(self) -> str:
        md_text: str = f"# {self._openapi.model.info.title}\n"
        for path, path_item in self._openapi.model.paths.items():
            for http_method, operation_model in path_item.items():
                if operation_model.deprecated:
                    md_text += f"### {I18n.Name}: ~~{operation_model.operation_id}~~\n"
                else:
                    md_text += f"### {I18n.Name}: {operation_model.operation_id}\n"
                head_text: str = self.gen_head_info(http_method, path, operation_model)
                if head_text:
                    md_text += head_text + "\n"
                md_text += self.gen_request_info(http_method, path, operation_model) + "\n"
                md_text += self.gen_response_info(http_method, path, operation_model) + "\n"
                tail_text: str = self.gen_tail_info(http_method, path, operation_model)
                if tail_text:
                    md_text += tail_text + "\n"
        return md_text
