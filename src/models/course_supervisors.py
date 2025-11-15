from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base

class CourseSupervisor(Base):
    __tablename__ = "course_supervisors"

    course_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("courses.id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    supervisor_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )

