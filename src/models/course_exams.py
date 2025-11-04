from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base

class CourseExam(Base):
    __tablename__ = "course_exams"

    exam_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("exams.id", ondelete="CASCADE"), 
        primary_key=True
    )
s
    course_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("courses.id", ondelete="CASCADE"), 
        primary_key=True
    )