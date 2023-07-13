# print(any_api_model_schema(aaa.Demo))
# print(any_api_model_schema(bbb.Demo))
# print(any_api_model_schema(response.UserSuccessRespModel.ResponseModel))
# print(any_api_model_schema(response.UserSuccessRespModel2.ResponseModel))
import json

from demo_v1 import response

# print(aaa.Demo.schema())
# print(bbb.Demo.schema())


print(json.dumps(response.UserSuccessRespModel.ResponseModel.schema()))

# from pydantic.schema import get_model_name_map, model_process_schema, get_flat_models_from_model
# from typing import Dict, Any
# todo_model = {
#     aaa.Demo,
#     bbb.Demo,
#     response.UserSuccessRespModel.ResponseModel,
#     response.UserSuccessRespModel2.ResponseModel,
# }
# flat_models = set()
# for model in todo_model:
#     flat_models |= get_flat_models_from_model(model)
# model_name_map = get_model_name_map(flat_models)
#
#
# definitions: Dict[str, Dict[str, Any]] = {}
# for model in flat_models:
#     m_schema, m_definitions, m_nested_models = model_process_schema(
#         model, model_name_map=model_name_map, ref_prefix="#/components/schemas/"
#     )
#     definitions.update(m_definitions)
#     model_name = model_name_map[model]
#
#     definitions[model_name] = m_schema
#
# import json
# print(model_name_map)
# print(json.dumps(definitions))
