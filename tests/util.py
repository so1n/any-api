import copy
from typing import Any, List

from example.pet_store import pet_store_openapi


def check_dict(
    *,
    nested_key_list: List[str],
    source_container: Any,
    target_container: Any,
    raw_source_container: Any,
    raw_target_container: Any,
    ignore_key_list: List[List[str]],
) -> None:
    if not isinstance(source_container, type(target_container)):
        raise ValueError("->".join(nested_key_list) + " type error")
    elif isinstance(source_container, dict):
        if "enum" in source_container:
            key_list: List[str] = target_container["allOf"][0]["$ref"].split("/")[1:]
            target_container = pet_store_openapi.dict
            for key in key_list:
                target_container = target_container[key]
            assert target_container["type"] == source_container["type"]
            assert sorted(target_container["enum"]) == sorted(source_container["enum"])
        else:
            for key, value in source_container.items():
                if nested_key_list + [key] in ignore_key_list:
                    continue
                if key not in target_container:
                    raise KeyError("->".join(nested_key_list) + f" not found key: {key} in {target_container}")
                new_nested_key_list = copy.copy(nested_key_list)
                new_nested_key_list.append(key)
                check_dict(
                    nested_key_list=new_nested_key_list,
                    source_container=value,
                    target_container=target_container[key],
                    ignore_key_list=ignore_key_list,
                    raw_source_container=raw_source_container,
                    raw_target_container=raw_target_container,
                )
    elif isinstance(source_container, list):
        if len(source_container) != len(target_container):
            raise ValueError(
                "->".join(nested_key_list) + f" container length not equal, {source_container} {target_container}"
            )
        for index in range(len(source_container)):
            check_dict(
                nested_key_list=nested_key_list,
                source_container=source_container[index],
                target_container=target_container[index],
                raw_target_container=raw_target_container,
                raw_source_container=raw_source_container,
                ignore_key_list=ignore_key_list,
            )
    else:
        if len(nested_key_list) >= 3 and nested_key_list[-1] == "description" and nested_key_list[-3] == "responses":
            # AnyAPI output: Successful operation|Successful operation, Pet store desc:  Successful operation
            # AnyAPI output: Successful operation|Successful operation, Pet store desc:  successful operation
            assert source_container.lower() in target_container.lower(), (
                "->".join(nested_key_list)
                + f" value error \n>>>>>>\nsource:\n\n{source_container}\n>>>>>>\ntarget:\n\n{target_container}\n>>>>>>"
            )
        else:
            assert source_container == target_container, (
                "->".join(nested_key_list)
                + f" value error \n>>>>>>\nsource:\n\n{source_container}\n>>>>>>\ntarget:\n\n{target_container}\n>>>>>>"
            )
