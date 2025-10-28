import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base

class UserMajor(Base):
    __tablename__ = "user_majors"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    major_id = Column(UUID(as_uuid=True), ForeignKey("majors.id"), primary_key=True)