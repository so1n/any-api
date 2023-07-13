from typing import List, Type

from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    code: int = Field(0, description="api code")
    msg: str = Field("success", description="api status msg")


class ResponseFailModel(ResponseModel):
    code: int = Field(1, description="api code")
    msg: str = Field("fail", description="api status msg")


class UserSuccessRespModel(BaseModel):
    class ResponseModel(ResponseModel):
        class DataModel(BaseModel):
            uid: int = Field(666, description="user id", gt=10, lt=1000)
            user_name: str = Field("mock_name", description="user name", min_length=2, max_length=10)
            age: int = Field(99, description="age", gt=1, lt=100)
            content_type: str = Field(description="content-type")

        data: DataModel

    description: str = "success response"
    response_data: Type[BaseModel] = ResponseModel


class UserSuccessRespModel2(BaseModel):
    class ResponseModel(ResponseModel):
        class DataModel(BaseModel):
            uid: int = Field(description="user id", gt=10, lt=1000, example=666)
            user_name: str = Field(example="mock_name", description="user name", min_length=2, max_length=10)
            multi_user_name: List[str] = Field(
                example=["mock_name"], description="user name", min_length=2, max_length=10
            )
            age: int = Field(example=99, description="age", gt=1, lt=100)
            email: str = Field(example="example@so1n.me", description="user email")

        data: DataModel

    description: str = "success response"
    response_data: Type[BaseModel] = ResponseModel
