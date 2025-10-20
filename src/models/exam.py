import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.api.database import Base 
import enum

class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    short_answer = "short_answer"
    long_answer = "long_answer"
    matching = "matching"

class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    expired = "expired"

class Exam(Base):
    __tablename__ = "exams"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    instructions = Column(String(2000))
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    max_attempts = Column(Integer, default=1)
    pass_threshold = Column(Integer, default=60)
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User")
    
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    question_type = Column(SQLAlchemyEnum(QuestionType), nullable=False)
    title = Column(String, nullable=False)
    points = Column(Integer, default=1)
    position = Column(Integer, default=0)
    
    exam = relationship("Exam", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")

class Option(Base):
    __tablename__ = "options"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")

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
    exam = relationship("Exam")
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