import json
import os
import pathlib

from example.pet_store import pet_store_openapi
from tests.util import check_dict


class TestPetStore:
    def test_pet_store(self) -> None:
        now_path = pathlib.Path(__file__).parent
        openapi_filename = os.path.join(now_path, "pet_store_openapi.json")
        with open(openapi_filename, "r") as f:
            pet_store_json = f.read()
        pet_store_dict = json.loads(pet_store_json.strip("\n"))

        check_dict(
            nested_key_list=[],
            ignore_key_list=[
                # any-api not support requestBodies
                ["components", "requestBodies"],
                # petstore not use Customer and address in api
                ["components", "schemas", "Customer"],
                ["components", "schemas", "Address"],
                # petstore ApiResponse only json response
                ["components", "schemas", "ApiResponse", "xml"],
            ],
            source_container=pet_store_dict,
            target_container=pet_store_openapi.dict,
            raw_source_container=pet_store_dict,
            raw_target_container=pet_store_openapi.dict,
        )
