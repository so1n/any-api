"""
Compatible with V1 and V 2 versions of pydantic
"""
from functools import partial
from typing import Any, Callable, Dict, Tuple, Type

from pydantic import BaseModel
from pydantic.version import VERSION

is_v1: bool = VERSION.startswith("1")
ModelNameMapType = Dict[Type[BaseModel], str]
DefinitionsReturnType = Tuple[ModelNameMapType, dict]


if is_v1:
    from pydantic import root_validator as _model_validator
    from pydantic import validator as _field_validator
    from pydantic.schema import get_flat_models_from_model, get_model_name_map, model_process_schema

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
            model_name = model_name_map[model]

            definitions[model_name] = m_schema
        return model_name_map, definitions

else:
    from pydantic import field_validator as _field_validator
    from pydantic import model_validator as _model_validator
    from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode

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
            any_api_model_name_map[k[0]] = v.replace(replace_str, "")
        return any_api_model_name_map, definitions


def model_json_schema(model: Type[BaseModel]) -> dict:
    if is_v1:
        schema_dict = model.schema()
        if "definitions" in schema_dict:
            schema_dict["$defs"] = schema_dict["definitions"]
    else:
        from pydantic.json_schema import model_json_schema

        schema_dict = model_json_schema(model)
    return schema_dict


def model_validator(*, mode: str) -> Callable:
    if mode == "before":
        if is_v1:
            return partial(_model_validator, pre=True)
        else:
            return _model_validator(mode=mode)
    else:
        raise RuntimeError(f"Not support `{mode}`")


def field_validator(*args: Any, **kwargs: Any) -> Callable:
    return partial(_field_validator, *args, **kwargs)
