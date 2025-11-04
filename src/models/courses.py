from sqlalchemy import Column, String, TIMESTAMP, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    code = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    students = relationship(
        "User",
        secondary="course_enrollments",
        back_populates="courses"
    )


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)