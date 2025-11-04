from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class CourseBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["Математичний аналіз"])
    description: Optional[str] = Field(None, max_length=2000, examples=["Основи диференціального числення."])
    code: str = Field(..., max_length=20, examples=["MA-101"])

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    code: Optional[str] = Field(None, max_length=20)

class Course(BaseModel):
    id: UUID               

    class Config:
        from_attributes = True

class CoursesPage(BaseModel):
    items: List[Course]
    total: int
    limit: int
    offset: int

class MyCourse(BaseModel):
    id: UUID
    name: str
    code: str
    student_count: int
    exam_count: int

    class Config:
        from_attributes = True
