from pydantic import BaseModel


class BaseAPIModel(BaseModel):
    openapi: str
    tags: list
    components: dict
