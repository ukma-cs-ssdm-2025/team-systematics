from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class CourseGpa(BaseModel):
    """GPA information for a single course."""
    id: UUID = Field(..., description="ID of the course/exam")
    course_name: str = Field(..., description="Course name")
    gpa: Optional[float] = Field(None, description="GPA / numeric grade for the course (0-100 scale)")


class CertificateGpaResponse(BaseModel):
    """Response model for GPA per course."""
    courses: List[CourseGpa]
