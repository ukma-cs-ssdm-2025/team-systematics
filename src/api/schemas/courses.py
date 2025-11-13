from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from .exams import ExamInList

class CourseBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=200, 
        examples=["Математичний аналіз"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=2000, 
        examples=["Основи диференціального та інтегрального числення."]
    )
    code: str = Field(
        ...,
        min_length=5, 
        max_length=5, 
        examples=["MA101"]
    )

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    code: Optional[str] = Field(None, max_length=20)

class Course(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    student_count: int = Field(..., examples=[35])
    exam_count: int = Field(..., examples=[3])
    is_enrolled: bool = False

    class Config:
        from_attributes = True

class CoursesPage(BaseModel):
    items: List[Course]
    total: int
    limit: int
    offset: int

class CourseSupervisorListItem(BaseModel):
    id: UUID
    name: str
    code: str
    students_count: int
    teachers: list[str]

class CourseSupervisorDetails(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str]
    students: list[dict]
    teachers: list[dict]

class CourseExamsPage(BaseModel):
    course_id: UUID
    course_name: str
    exams: List[ExamInList]
