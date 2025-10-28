from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from src.api.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)  # INTEGER
    title = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    enrollments = relationship(
        "CourseEnrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)  # INTEGER
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)  # INTEGER FK
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # UUID FK

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_user"),
    )

    course = relationship("Course", back_populates="enrollments")