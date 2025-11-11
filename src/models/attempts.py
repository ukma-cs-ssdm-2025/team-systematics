import uuid
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum as SQLAlchemyEnum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.api.database import Base
import enum

class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    completed = "completed"

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(SQLAlchemyEnum(AttemptStatus), default=AttemptStatus.in_progress)
    started_at = Column(DateTime, nullable=False)
    due_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime)
    earned_points = Column(Float, nullable=True, comment="Точна фінальна оцінка (напр., 85.71)")
    time_spent_seconds = Column(Integer, nullable=True)
    correct_answers = Column(Integer, nullable=True)
    incorrect_answers = Column(Integer, nullable=True)
    pending_count = Column(Integer, nullable=True)
    
    user = relationship("User", back_populates="attempts") 
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")
    plagiarism_check = relationship("PlagiarismCheck", back_populates="attempt", uselist=False)

class Answer(Base):
    __tablename__ = "answers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String, nullable=True)
    answer_json = Column(JSONB, nullable=True)
    saved_at = Column(TIMESTAMP(timezone=True), nullable=False)
    earned_points = Column(Float, nullable=True, comment="Оцінка за це питання (для long_answer встановлюється вручну вчителем)")
    
    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question")
    selected_options = relationship("AnswerOption", back_populates="answer", cascade="all, delete-orphan")

class AnswerOption(Base):
    __tablename__ = "answer_options"
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), primary_key=True)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"), primary_key=True)

    answer = relationship("Answer", back_populates="selected_options")

class PlagiarismStatus(str, enum.Enum):
    ok = "ok"
    suspicious = "suspicious"
    high_risk = "high_risk"

class PlagiarismCheck(Base):
    __tablename__ = "plagiarism_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False, unique=True)
    uniqueness_percent = Column(Float, nullable=False)
    max_similarity = Column(Float, nullable=False)
    status = Column(SQLAlchemyEnum(PlagiarismStatus), nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    attempt = relationship("Attempt", back_populates="plagiarism_check")
