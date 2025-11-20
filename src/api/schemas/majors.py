from pydantic import BaseModel

class MajorResponse(BaseModel):
    """Схема для відображення спеціальності."""
    id: int
    name: str

    class Config:
        from_attributes = True

