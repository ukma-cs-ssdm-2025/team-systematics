import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base

class Major(Base):
    __tablename__="majors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)

    users = relationship(
        "User", 
        secondary="user_majors",
        back_populates="major"
    )