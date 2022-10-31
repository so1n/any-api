from pydantic import BaseModel, Field


class BaseAPIModel(BaseModel):
    openapi: str
    tags: list
    components: dict = Field(default_factory=dict)
