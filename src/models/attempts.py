import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.api.database import Base
import enum

class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    expired = "expired"

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(SQLAlchemyEnum(AttemptStatus), default=AttemptStatus.in_progress)
    started_at = Column(DateTime, nullable=False)
    due_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime)
    score_percent = Column(Integer)
    
    user = relationship("User")
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String, nullable=True)
    answer_json = Column(JSONB, nullable=True)
    saved_at = Column(TIMESTAMP(timezone=True), nullable=False) 
    
    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question")
    selected_options = relationship("AnswerOption", cascade="all, delete-orphan")

class AnswerOption(Base):
    __tablename__ = "answer_options"
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), primary_key=True)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"), primary_key=True)