from enum import Enum
from typing import Any, List, Type

from pydantic import BaseModel, Field

from any_api.openapi.model import ApiModel, links
from any_api.openapi.model import openapi as openapi_model
from any_api.openapi.openapi_v1 import OpenAPI, requests, responses


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


class SimpleRespModel(responses.JsonResponseModel):
    class ResponseModel(BaseModel):
        code: int = Field(0, description="api code")
        msg: str = Field("success", description="api status msg")
        data: dict = Field(description="success result")

    description: str = "success response"
    response_data: Type[BaseModel] = ResponseModel


class TextRespModel(responses.TextResponseModel):
    class HeaderModel(BaseModel):
        x_example_type: str = Field(default="text", alias="X-Example-Type")

    header: BaseModel = HeaderModel
    description: str = "text response"


class HtmlRespModel(responses.HtmlResponseModel):
    class HeaderModel(BaseModel):
        x_example_type: str = Field(default="html", alias="X-Example-Type")

    header: BaseModel = HeaderModel
    description: str = "html response"


class FileRespModel(responses.FileResponseModel):
    class HeaderModel(BaseModel):
        x_example_type: str = Field(default="file", alias="X-Example-Type")

    header: BaseModel = HeaderModel
    description: str = "file response"


# response model
class ResponseModel(BaseModel):
    code: int = Field(0, description="api code")
    msg: str = Field("success", description="api status msg")


class UserSuccessRespModel(responses.JsonResponseModel):
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
        ApiModel(
            path="/api/user/info",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="get request demo",
            operation_id="get",
            request_dict={
                "query": [requests.RequestModel(model=DemoUserDataModel)],
                "header": [requests.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def text_response_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/resp/text",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="text response demo",
            operation_id="text response",
            response_list=[TextRespModel],
        )
    )


def file_response_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/resp/file",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="file response demo",
            operation_id="file response",
            response_list=[FileRespModel],
        )
    )


def html_response_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/resp/html",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="html response demo",
            operation_id="html response",
            response_list=[HtmlRespModel],
        )
    )


def cookie_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/user/extra-info",
            http_method_list=["get"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="cookie request demo",
            operation_id="cookie",
            request_dict={"cookie": [requests.RequestModel(model=HeaderModel)]},
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def file_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/user/upload-file",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="file request demo",
            operation_id="file",
            request_dict={
                "file": [requests.RequestModel(media_type_list=["multipart/form-data"], model=FileModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def form_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/user/info-form",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="form request demo",
            operation_id="form",
            request_dict={
                "form": [
                    requests.RequestModel(
                        media_type_list=["application/x-www-form-urlencoded"], model=DemoUserDataModel
                    )
                ],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def multiform_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/user/info-multiform",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="multiform request demo",
            operation_id="multiform",
            request_dict={
                "multiform": [
                    requests.RequestModel(
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
        ApiModel(
            path="/api/user/borrow-book",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            summary="post request demo",
            operation_id="post",
            request_dict={
                "body": [
                    requests.RequestModel(media_type_list=["application/json"], model=DemoUserDataModel),
                    requests.RequestModel(media_type_list=["application/json"], model=BookModel),
                ],
                "header": [requests.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def post_and_has_query_request_openapi_example(openapi: OpenAPI) -> None:
    openapi.add_api_model(
        ApiModel(
            path="/api/user/borrow-book/v2",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="post_and_has_query",
            summary="post and has query request demo",
            request_dict={
                "query": [requests.RequestModel(model=BookModel)],
                "body": [requests.RequestModel(media_type_list=["application/json"], model=DemoUserDataModel)],
                "header": [requests.RequestModel(model=HeaderModel)],
            },
            response_list=[SimpleRespModel, UserSuccessRespModel],
        )
    )


def link_example(openapi: OpenAPI) -> None:
    class LoginRespModel(responses.JsonResponseModel):
        class ResponseModel(BaseModel):  # type: ignore
            class DataModel(BaseModel):
                token: str

            code: int = Field(0, description="api code")
            msg: str = Field("success", description="api status msg")
            data: DataModel

        description: str = "login response"
        response_data: Type[BaseModel] = ResponseModel

    class LoginModel(BaseModel):
        user: str = Field(description="user")
        password: str = Field(description="user password")

    class HeaderWithLinkModel(BaseModel):
        token: str = Field(
            description="Token to be carried by the user to access the interface",
            links=links.LinksModel(LoginRespModel, "$response.body#/data/token", desc="test links model"),
        )

    openapi.add_api_model(
        ApiModel(
            path="/api/user/logout",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="user logout",
            summary="user logout demo",
            request_dict={"header": [requests.RequestModel(model=HeaderWithLinkModel)]},
            response_list=[SimpleRespModel],
        ),
        ApiModel(
            path="/api/user/login",
            http_method_list=["post"],
            tags=[openapi_model.TagModel(name="demo", description="test request")],
            operation_id="user login",
            summary="user login demo",
            request_dict={
                "body": [requests.RequestModel(media_type_list=["application/json"], model=LoginModel)],
            },
            response_list=[LoginRespModel],
        ),
    )


if __name__ == "__main__":
    my_openapi: OpenAPI = OpenAPI()
    html_response_openapi_example(my_openapi)
    file_response_openapi_example(my_openapi)
    text_response_openapi_example(my_openapi)
    get_request_openapi_example(my_openapi)
    cookie_request_openapi_example(my_openapi)
    file_request_openapi_example(my_openapi)
    form_request_openapi_example(my_openapi)
    multiform_request_openapi_example(my_openapi)
    post_request_openapi_example(my_openapi)
    post_and_has_query_request_openapi_example(my_openapi)
    link_example(my_openapi)
    print(my_openapi.content())
    # from any_api.openapi.to.markdown import Markdown
    #
    # print(Markdown(my_openapi).content)
