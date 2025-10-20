import uuid
from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import UUID
from src.api.database import Base

class MatchingOption(Base):
    __tablename__ = 'matching_pairs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), nullable=False)
    prompt = Column(Text, nullable=False)
    correct_match = Column(Text, nullable=False)