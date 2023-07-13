from pydantic import BaseModel, Field


class Demo(BaseModel):
    a: str = Field()
    b: str = Field()
