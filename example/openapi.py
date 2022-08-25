from enum import Enum
from typing import List, Type
from any_api.openapi.openapi import OpenAPI, request_model, openapi_model, response_model
from pydantic import BaseModel, Field


class SexEnum(str, Enum):
    man: str = "man"
    woman: str = "woman"


class HeaderModel(BaseModel):
    token: str = Field(description="Token to be carried by the user to access the interface")


class SimpleModel(BaseModel):
    uid: int = Field(description="user id", gt=10, lt=1000, example=666)
    user_name: str = Field(example="mock_name", description="user name", min_length=2, max_length=10)


class BookModel(BaseModel):
    isbn: str = Field(description="book isbn")
    name: str = Field(description="book name")


class DemoUserDataModel(SimpleModel):
    class ExtendInfoModel(BaseModel):
        multi_user_name: List[str] = Field(
            example=["mock_name"], description="user name", min_length=2, max_length=10
        )
        sex: SexEnum = Field(example=SexEnum.man, description="sex")
        age: int = Field(example=99, description="age", gt=1, lt=100)
        email: str = Field(example="example@so1n.me", description="user email")

    extend_info: ExtendInfoModel

    class Config:
        use_enum_values = True


class SimpleRespModel(response_model.JsonResponseModel):
    class ResponseModel(BaseModel):
        code: int = Field(0, description="api code")
        msg: str = Field("success", description="api status msg")
        data: dict = Field(description="success result")

    description: str = "success response"
    response_data: Type[BaseModel] = ResponseModel


class TextRespModel(response_model.TextResponseModel):
    header: dict = {"X-Example-Type": "text"}
    description: str = "text response"


class HtmlRespModel(response_model.HtmlResponseModel):
    header: dict = {"X-Example-Type": "html"}
    description: str = "html response"


class FileRespModel(response_model.FileResponseModel):
    header: dict = {"X-Example-Type": "file"}
    description: str = "file response"


# response model
class ResponseModel(BaseModel):
    code: int = Field(0, description="api code")
    msg: str = Field("success", description="api status msg")


class UserSuccessRespModel(response_model.JsonResponseModel):
    class ResponseModel(ResponseModel):  # type: ignore
        class DataModel(BaseModel):
            uid: int = Field(description="user id", gt=10, lt=1000, example=666)
            user_name: str = Field(example="mock_name", description="user name", min_length=2, max_length=10)
            multi_user_name: List[str] = Field(
                example=["mock_name"], description="user name", min_length=2, max_length=10
            )
            sex: SexEnum = Field(example=SexEnum.man, description="sex")
            age: int = Field(example=99, description="age", gt=1, lt=100)
            email: str = Field(example="example@so1n.me", description="user email")

            class Config:
                use_enum_values = True

        data: DataModel

    description: str = "success response"
    response_data: Type[BaseModel] = ResponseModel


def get_request_openapi_example() -> str:
    return OpenAPI.build().add_invoke_model(
        request_model.InvokeModel(
            path="/api/user/info",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="123",
            request_dict={
                "query": [request_model.RequestModel(model=DemoUserDataModel)],
                "header": [request_model.RequestModel(model=HeaderModel)]
            },
            response_list=[SimpleRespModel, UserSuccessRespModel]
        )
    ).content()


def post_request_openapi_example() -> str:
    return OpenAPI.build().add_invoke_model(
        request_model.InvokeModel(
            path="/api/user/borrow-book",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="123",
            request_dict={
                "body": [
                    request_model.RequestModel(media_type="application/json", model=DemoUserDataModel),
                    request_model.RequestModel(media_type="application/json", model=BookModel)
                ],
                "header": [request_model.RequestModel(model=HeaderModel)]
            },
            response_list=[SimpleRespModel, UserSuccessRespModel]
        )
    ).content()


def post_and_has_query_request_openapi_example() -> str:
    return OpenAPI.build().add_invoke_model(
        request_model.InvokeModel(
            path="/api/user/borrow-book",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="123",
            request_dict={
                "query": [request_model.RequestModel(model=BookModel)],
                "body": [request_model.RequestModel(media_type="application/json", model=DemoUserDataModel)],
                "header": [request_model.RequestModel(model=HeaderModel)]
            },
            response_list=[SimpleRespModel, UserSuccessRespModel]
        )
    ).content()


if __name__ == "__main__":
    print(get_request_openapi_example())
    print(post_request_openapi_example())
    print(post_and_has_query_request_openapi_example())