from pydantic.json_schema import GenerateJsonSchema, model_json_schema

from demo_v1 import response

instance = GenerateJsonSchema(by_alias=True, ref_template="#/definitions/{model}")
import json

print(json.dumps(model_json_schema(response.UserSuccessRespModel.ResponseModel)))

# result = instance.generate_definitions(
#     [
#         (model, "validation", model.__pydantic_core_schema__)
#         for model in [
#             response.UserSuccessRespModel.ResponseModel, response.UserSuccessRespModel2.ResponseModel,
#             aaa.Demo, bbb.Demo
#         ]
#     ]
# )
# new_dict = {}
# for k,v in result[0].items():
#     new_dict[k[0]] = v["$ref"].replace("#/definitions/", "")
# print(new_dict)
# import json
# print(json.dumps(result[1]))
#
#
# # print(model_json_schema(response.UserSuccessRespModel.ResponseModel, ref_template="#/definitions/{model}"))
# # print(model_json_schema(response.UserSuccessRespModel2.ResponseModel, ref_template="#/definitions/{model}"))
#
# # schema_1 = model_json_schema(ccc.Demo, ref_template="#/definitions/{model}")
# # if "$defs" in schema_1:
# #     schema_1["definitions"] = schema_1.pop("$defs")
# # import json
# # print(json.dumps(schema_1))
#
# # instance = GenerateJsonSchema(by_alias=True, ref_template="#/definitions/{model}")
# #
# # for model in [response.UserSuccessRespModel.ResponseModel, response.UserSuccessRespModel2.ResponseModel]:
# #     json_schemas_map, definitions = instance.generate_definitions([(model, "serialization", model.__pydantic_core_schema__)])
# #     print(json_schemas_map)
# #     print(definitions)
# #     print()
# #     instance._used = False
# # schema1 = definitions.pop("any_api__aaa__ccc__Demo")
# # schema1["definitions"] = definitions
# # print(json.dumps(schema1))
# # instance._used = False
