from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.api.database import Base, get_json_type
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    patronymic = Column(String)
    notification_settings = Column(
        get_json_type(), 
        nullable=False, 
        server_default=text("'{\"enabled\": false, \"remind_before_hours\": []}'")
    )
    avatar_url = Column(String(255), nullable=True)
    
    major = relationship(
        "Major", 
        secondary="user_majors",
        back_populates="users",
        uselist=False
    )

    courses = relationship(
        "Course",
        secondary="course_enrollments",
        back_populates="students"
    )

    attempts = relationship("Attempt", back_populates="user")
