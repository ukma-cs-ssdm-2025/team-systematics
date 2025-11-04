import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.api.database import Base
from src.models.matching_options import MatchingOption 
import enum

class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    short_answer = "short_answer"
    long_answer = "long_answer"
    matching = "matching"

class QuestionTypeWeight(Base):
    __tablename__ = 'question_type_weights'
    question_type = Column( SQLAlchemyEnum(
            QuestionType,
            name="question_type_enum_weights",
            create_type=False),
            primary_key=True
    )
    weight = Column(Integer, nullable=False, default=1)

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
    attempts = relationship("Attempt", back_populates="exam")
    courses = relationship("Course", secondary="course_exams", back_populates="exams")

class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    question_type = Column(SQLAlchemyEnum(QuestionType), nullable=False)
    title = Column(String, nullable=False)
    points = Column(Integer, nullable=True)
    position = Column(Integer, default=0)
    
    exam = relationship("Exam", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")
    matching_options = relationship("MatchingOption", 
                                    foreign_keys=[MatchingOption.question_id], 
                                    primaryjoin="Question.id == MatchingOption.question_id",
                                    cascade="all, delete-orphan")


class Option(Base):
    __tablename__ = "options"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")