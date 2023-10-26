"""
Compatible with V1 and V 2 versions of pydantic
"""
from enum import Enum
from functools import partial
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from pydantic import BaseConfig, BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic.version import VERSION

is_v1: bool = VERSION.startswith("1")
ModelNameMapType = Dict[Type[BaseModel], str]
DefinitionsReturnType = Tuple[ModelNameMapType, dict]

__all__ = [
    # var
    "is_v1",
    "ModelNameMapType",
    "DefinitionsReturnType",
    "VERSION",
    "ConfigDict",
    # pydantic compat func
    "get_model_definitions",
    "model_json_schema",
    "model_validator",
    "model_dump",
    "field_validator",
    "model_fields",
    # util func
    "get_extra_by_field_info",
    "get_extra_dict_by_field_info",
    "create_pydantic_model",
    "json_type_default_value_dict",
    "gen_example_dict_from_schema",
    "remove_any_of",
]


if is_v1:
    from pydantic import root_validator as _model_validator
    from pydantic import validator as _field_validator
    from pydantic.fields import ModelField
    from pydantic.schema import get_flat_models_from_model, get_model_name_map, model_process_schema

    ConfigDict = dict

    def get_model_definitions(
        *model_sequence: Type[BaseModel], ref_prefix: str = "#/components/schemas/"
    ) -> DefinitionsReturnType:
        flat_models = set()
        for model in model_sequence:
            flat_models |= get_flat_models_from_model(model)
        model_name_map = get_model_name_map(flat_models)

        definitions: Dict[str, Dict[str, Any]] = {}
        for model in flat_models:
            m_schema, m_definitions, m_nested_models = model_process_schema(
                model, model_name_map=model_name_map, ref_prefix=ref_prefix
            )
            definitions.update(m_definitions)
            if model not in model_name_map:
                raise ValueError(
                    f"The current model may be a dynamically created model with a non-unique name."
                    f" module:{model.__module__}, name:{model.__name__}"
                )
            model_name = model_name_map[model]

            definitions[model_name] = m_schema
        return model_name_map, definitions

    def model_fields(model: Type[BaseModel]) -> Dict[str, ModelField]:
        return model.__fields__

    def get_field_info(field: ModelField) -> FieldInfo:
        return field.field_info

    def field_validator(*fields: str, mode: str = "after", **kwargs) -> Callable[[Any], Any]:  # type: ignore
        if "pre" not in kwargs:
            if mode == "before":
                pre = True
            elif mode == "after":
                pre = False
            else:
                raise ValueError(f"Not support mode: `{mode}`")
            kwargs["pre"] = pre
        return _field_validator(*fields, **kwargs)

else:
    from pydantic import ConfigDict as _ConfigDict
    from pydantic import field_validator as _field_validator
    from pydantic import model_validator as _model_validator
    from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode

    ConfigDict = _ConfigDict  # type: ignore[misc]

    def get_model_definitions(  # type: ignore[misc]
        *model_sequence: Type[BaseModel],
        ref_prefix: str = "#/components/schemas/{model}",
        mode: JsonSchemaMode = "validation",
    ) -> DefinitionsReturnType:
        generate_instance = GenerateJsonSchema(by_alias=True, ref_template=ref_prefix)
        model_name_map, definitions = generate_instance.generate_definitions(
            [(model, mode, model.__pydantic_core_schema__) for model in model_sequence]
        )
        any_api_model_name_map = {}
        replace_str = ref_prefix.split("{")[0]
        for k, v in model_name_map.items():
            any_api_model_name_map[k[0]] = v["$ref"].replace(replace_str, "")
        return any_api_model_name_map, definitions

    def model_fields(model: Type[FieldInfo]) -> Dict[str, FieldInfo]:
        return model.model_fields

    def get_field_info(field: FieldInfo) -> FieldInfo:
        return field

    field_validator = _field_validator  # type: ignore


def model_json_schema(model: Type[BaseModel], definition_key: str = "$defs") -> dict:
    if is_v1:
        schema_dict = model.schema()
        if "definitions" in schema_dict and definition_key != "definitions":
            schema_dict[definition_key] = schema_dict["definitions"]
    else:
        from pydantic.json_schema import model_json_schema

        schema_dict = model_json_schema(model)
        if "$defs" in schema_dict and definition_key != "$defs":
            schema_dict[definition_key] = schema_dict["$defs"]
    return schema_dict


def model_dump(model: BaseModel, **kwargs: Any) -> dict:
    if is_v1:
        return model.dict(**kwargs)
    else:
        return model.model_dump(**kwargs)


def model_validator(**kwargs: Any) -> Callable:
    if is_v1:
        if "mode" in kwargs:
            mode = kwargs.pop("mode")
            if mode == "before":
                kwargs["pre"] = True
            elif mode == "after":
                kwargs["pre"] = False
            else:
                raise ValueError(f"Not support mode:{mode}")
        return partial(_model_validator, **kwargs)
    else:
        if "pre" in kwargs:
            kwargs["mode"] = "before" if kwargs["pre"] is True else "after"
            kwargs.pop("pre")
        return _model_validator(**kwargs)


def get_extra_by_field_info(field: Any) -> Union[Callable, dict]:
    if is_v1:
        extra_dict: dict = field.field_info.extra
    else:
        extra_dict = field.json_schema_extra or {}
    return extra_dict


def create_pydantic_model(
    annotation_dict: Optional[Dict[str, Tuple[Type, Any]]] = None,
    class_name: str = "DynamicModel",
    pydantic_config: Optional[Type["BaseConfig"]] = None,
    pydantic_base: Optional[Type["BaseModel"]] = None,
    pydantic_module: str = "pydantic.main",
    pydantic_validators: Optional[Dict[str, classmethod]] = None,
) -> Type["BaseModel"]:
    """pydantic self.pait_response_model helper
    if use create_model('DynamicModel', **annotation_dict), mypy will tip error
    """
    return create_model(
        class_name,
        __config__=pydantic_config,
        __base__=pydantic_base,
        __module__=pydantic_module,
        __validators__=pydantic_validators,
        **(annotation_dict or {}),
    )


json_type_default_value_dict: Dict[str, Any] = {
    "null": None,
    "bool": True,
    "boolean": True,
    "string": "",
    "number": 0.0,
    "float": 0.0,
    "integer": 0,
    "object": {},
    "array": [],
}


def _example_value_handle(example_value: Any) -> Any:
    if getattr(example_value, "__call__", None):
        example_value = example_value()
    elif isinstance(example_value, Enum):
        example_value = example_value.value
    return example_value


def gen_example_dict_from_schema(
    schema_dict: Dict[str, Any],
    definition_dict: Optional[dict] = None,
    example_value_handle: Callable[[Any], Any] = _example_value_handle,
) -> Dict[str, Any]:
    gen_dict: Dict[str, Any] = {}

    def _ref_handle(_key: str, _value_dict: dict) -> None:
        if "items" in _value_dict:
            model_key: str = _value_dict["items"]["$ref"].split("/")[-1]
        else:
            model_key = _value_dict["$ref"].split("/")[-1]
        model_dict: dict = _definition_dict.get(model_key, {})
        if "enum" in model_dict:
            gen_dict[_key] = model_dict["enum"][0]
        elif model_dict.get("type", None) == "object":
            gen_dict[_key] = gen_example_dict_from_schema(
                _definition_dict.get(model_key, {}), _definition_dict, example_value_handle
            )
        else:
            gen_dict[_key] = [
                gen_example_dict_from_schema(
                    _definition_dict.get(model_key, {}), _definition_dict, example_value_handle
                )
            ]

    if "properties" not in schema_dict:
        return gen_dict
    property_dict: Dict[str, Any] = schema_dict["properties"]
    if not definition_dict:
        _definition_dict: dict = schema_dict.get("definitions", {})
    else:
        _definition_dict = definition_dict
    for key, value in property_dict.items():
        if "items" in value and value["type"] == "array":
            if "$ref" in value["items"]:
                _ref_handle(key, value)
            elif "example" in value:
                gen_dict[key] = example_value_handle(value["example"])
            elif "default" in value:
                gen_dict[key] = value["default"]
            else:
                gen_dict[key] = []
        elif "$ref" in value:
            _ref_handle(key, value)
        else:
            if "example" in value:
                gen_dict[key] = example_value_handle(value["example"])
            elif "default" in value:
                gen_dict[key] = value["default"]
            else:
                if "type" in value:
                    if value["type"] not in json_type_default_value_dict:
                        raise KeyError(f"Can not found type: {key} in json type")
                    gen_dict[key] = json_type_default_value_dict[value["type"]]
                else:
                    gen_dict[key] = "object"
            if isinstance(gen_dict[key], Enum):
                gen_dict[key] = gen_dict[key].value
    return gen_dict


def remove_any_of(schema_dict: dict) -> None:
    """
    Fix issue:  https://github.com/pydantic/pydantic/issues/6647
    remove schema anyOf key

    e.g.:
        code:
            class SubDemo(BaseModel):
                a: int = Field()

            class Demo(BaseModel):
                a: SubDemo

        pydantic v1 output:
            {
                'title': 'Demo',
                'type': 'object',
                'properties': {'a': {'$ref': '#/definitions/SubDemo'}},
                'definitions': {
                    'SubDemo': {
                        'title': 'SubDemo',
                        'type': 'object',
                        'properties': {'a': {'title': 'A', 'type': 'integer'}},
                        'required': ['a']}
                }
            }

        pydantic v2 output:
            {
                '$defs': {
                    'SubDemo': {
                        'properties': {'a': {'title': 'A', 'type': 'integer'}},
                        'required': ['a'],
                        'title': 'SubDemo',
                        'type': 'object'
                    }
                },
                'properties': {'a': {'anyOf': [{'$ref': '#/$defs/SubDemo'}, {'type': 'null'}]}},
                'required': ['a'],
                'title': 'Demo',
                'type': 'object'
            }
    """
    for k in list(schema_dict.keys()):
        v = schema_dict[k]
        if isinstance(v, dict):
            if "anyOf" in v:
                any_of_sub_value = {}
                any_of_value = v["anyOf"]
                if len(any_of_value) == 2:
                    if any_of_value[0].get("type", "") == "null":
                        any_of_sub_value = any_of_value[1]
                    elif any_of_value[1].get("type", "") == "null":
                        any_of_sub_value = any_of_value[0]

                if "$ref" in any_of_sub_value:
                    v.update(any_of_sub_value)
                    v.pop("anyOf")
                elif "items" in any_of_sub_value and "$ref" in any_of_sub_value["items"]:
                    # some like:
                    # {
                    #   'tags':
                    #       {
                    #           'anyOf': [
                    #               {'items': {'$ref': '#/components/schemas/Tag'}, 'type': 'array'},
                    #               {'type': 'null'}
                    #            ],
                    #            'default': None,
                    #            'title': 'Tags'
                    #       }
                    # }
                    v.update(any_of_sub_value)
                    v.pop("anyOf")
            else:
                remove_any_of(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    remove_any_of(item)


def get_extra_dict_by_field_info(field: Any, json_schema_extra_dict: Optional[dict] = None) -> dict:
    json_schema_extra = get_extra_by_field_info(field)
    if callable(json_schema_extra):
        if not json_schema_extra_dict:
            json_schema_extra_dict = {}
        json_schema_extra(json_schema_extra_dict)
    else:
        json_schema_extra_dict = json_schema_extra
    return json_schema_extra_dict
