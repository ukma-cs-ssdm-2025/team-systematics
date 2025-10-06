from pydantic import BaseModel, Field, conint
from typing import Literal

Role = Literal["student", "instructor", "admin"]

class Pagination(BaseModel):
    limit: conint(ge=1, le=100) = Field(10, description="Max items to return (1..100)")
    offset: conint(ge=0) = Field(0, description="Items to skip for pagination")