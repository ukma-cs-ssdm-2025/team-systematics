from pydantic import BaseModel, Field
from typing import Optional, List

class CourseBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

class Course(BaseModel):
    id: int               
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CoursesPage(BaseModel):
    items: List[Course]
    total: int
    limit: int
    offset: int

class MyCourse(BaseModel):
    id: int               
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
