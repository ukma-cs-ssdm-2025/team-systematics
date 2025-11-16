from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from src.api.database import Base

class Major(Base):
    __tablename__="majors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    users = relationship(
        "User", 
        secondary="user_majors",
        back_populates="major"
    )