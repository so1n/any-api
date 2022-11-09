from enum import Enum
from typing import Any, List, Type

from pydantic import BaseModel, Field

from any_api.openapi.model import openapi as openapi_model
from any_api.openapi.openapi import OpenAPI, request_model, response_model


class SexEnum(str, Enum):
    man: str = "man"
    woman: str = "woman"


class HeaderModel(BaseModel):
    token: str = Field(description="Token to be carried by the user to access the interface")


class SimpleModel(BaseModel):
    uid: int = Field(description="user id", gt=10, lt=1000, example=666)
    user_name: str = Field(example="mock_name", description="user name", min_length=2, max_length=10)


class MultiFromModel(BaseModel):
    mobile: List[str] = Field(description="Mobile")


class FileModel(BaseModel):
    upload_file: Any = Field(description="uploaded file")


class BookModel(BaseModel):
    isbn: str = Field(description="book isbn")
    name: str = Field(description="book name")


class DemoUserDataModel(SimpleModel):
    class ExtendInfoModel(BaseModel):
        multi_user_name: List[str] = Field(example=["mock_name"], description="user name", min_length=2, max_length=10)
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


def get_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/info",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="get request demo",
            operation_id="get",
            request_dict={
                "query": [request_model.RequestModel(model=DemoUserDataModel)],
                "header": [request_model.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def cookie_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/extra-info",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="cookie request demo",
            operation_id="cookie",
            request_dict={"cookie": [request_model.RequestModel(model=HeaderModel)]},
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def file_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/upload-file",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="file request demo",
            operation_id="file",
            request_dict={
                "file": [request_model.RequestModel(media_type_list=["multipart/form-data"], model=FileModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def form_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/info-form",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="form request demo",
            operation_id="form",
            request_dict={
                "form": [
                    request_model.RequestModel(
                        media_type_list=["application/x-www-form-urlencoded"], model=DemoUserDataModel
                    )
                ],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def multiform_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/info-multiform",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="multiform request demo",
            operation_id="multiform",
            request_dict={
                "multiform": [
                    request_model.RequestModel(
                        media_type_list=["application/x-www-form-urlencoded"],
                        openapi_serialization={"style": "form", "explode": True},
                        model=MultiFromModel,
                    )
                ],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def post_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/borrow-book",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="post request demo",
            operation_id="post",
            request_dict={
                "body": [
                    request_model.RequestModel(media_type_list=["application/json"], model=DemoUserDataModel),
                    request_model.RequestModel(media_type_list=["application/json"], model=BookModel),
                ],
                "header": [request_model.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def post_and_has_query_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        request_model.ApiModel(
            path="/api/user/borrow-book/v2",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="post_and_has_query",
            summary="post and has query request demo",
            request_dict={
                "query": [request_model.RequestModel(model=BookModel)],
                "body": [request_model.RequestModel(media_type_list=["application/json"], model=DemoUserDataModel)],
                "header": [request_model.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


if __name__ == "__main__":
    my_openapi: OpenAPI = OpenAPI()
    get_request_openapi_example(my_openapi)
    cookie_request_openapi_example(my_openapi)
    file_request_openapi_example(my_openapi)
    form_request_openapi_example(my_openapi)
    multiform_request_openapi_example(my_openapi)
    post_request_openapi_example(my_openapi)
    post_and_has_query_request_openapi_example(my_openapi)
    print(my_openapi.content())
    from any_api.openapi.to.markdown import Markdown

    print(Markdown(my_openapi).content)
