from pydantic import BaseModel, Field


class Demo(BaseModel):
    a: int = Field()
    b: int = Field()
