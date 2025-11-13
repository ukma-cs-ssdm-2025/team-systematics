from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field, conint, constr, validator
from src.models.exams import ExamStatusEnum

DEFAULT_END_AT_EXAMPLE = "2027-10-08T10:00:00Z"
DEFAULT_INSTRUCTIONS = "Іспит складається з 20 теоретичних питань."
EXAMPLE_TITLE = "Вступ до Docker"

def datetime_must_not_be_in_past(cls, v):
    """Перевіряє, що дата/час не в минулому відносно поточного часу.

    Args:
        v: Значення поля datetime, яке проходить валідацію.

    Returns:
        Не змінене значення, якщо валідація успішна.

    Raises:
        ValueError: Якщо дата/час в минулому.
    """
    if v:
        now = datetime.now(timezone.utc)
        # Якщо datetime не має timezone, вважаємо його UTC
        v_with_tz = v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v
        if v_with_tz < now:
            raise ValueError("Дата та час не можуть бути в минулому")
    return v

def end_at_must_be_after_start_at(cls, v, values):
    """Перевіряє, що дата завершення (`end_at`) наступає після дати початку (`start_at`).

    Args:
        v: Значення поля `end_at`, яке проходить валідацію.
        values: Словник значень інших полів моделі, які вже пройшли валідацію.

    Returns:
        Не змінене значення `end_at`, якщо валідація успішна.

    Raises:
        ValueError: Якщо `end_at` є раніше або збігається з `start_at`.
    """
    if "start_at" in values and values["start_at"] and v:
        if v <= values["start_at"]:
            raise ValueError("end_at must be after start_at")
    return v

class ExamCreate(BaseModel):
    title: constr(min_length=3, max_length=100) = Field( # type: ignore
        ...,
        description="Exam title",
        example=EXAMPLE_TITLE,
    )
    instructions: Optional[constr(max_length=2000)] = Field( # type: ignore
        None,
        description="Markdown/HTML instructions",
        example=DEFAULT_INSTRUCTIONS
    )
    start_at: datetime = Field(
        ...,
        example="2026-10-08T10:00:00Z",
        description="Start datetime (UTC)"
    )
    end_at: datetime = Field(
        ...,
        example=DEFAULT_END_AT_EXAMPLE,
        description="End datetime (UTC)"
    )
    duration_minutes: int = Field(
        60,
        description="Duration of the exam in minutes",
        example=120
    )
    max_attempts: conint(ge=1, le=10) = Field( # type: ignore
        1,
        description="Max attempts per user",
        example=3
    )
    pass_threshold: conint(ge=0, le=100) = Field( # type: ignore
        60,
        description="Passing threshold in percent",
        example=75
    )
    owner_id: Optional[UUID] = Field(
        None,
        description="Instructor user id (automatically set from token if not provided)",
        example="c7a1c7e2-4a2c-4b6e-8e7f-9d3c5f2b1a8e"
    )

    _validate_start_at_not_in_past = validator("start_at", allow_reuse=True)(datetime_must_not_be_in_past)
    _validate_end_at_not_in_past = validator("end_at", allow_reuse=True)(datetime_must_not_be_in_past)
    _validate_dates = validator("end_at", allow_reuse=True)(end_at_must_be_after_start_at)

class ExamUpdate(BaseModel):
    title: Optional[constr(min_length=3, max_length=100)] = Field( # type: ignore
        None,
        description="Exam title",
        example="Docker: Просунутий рівень"
    )
    instructions: Optional[constr(max_length=2000)] = Field( # type: ignore
        None,
        description="Markdown/HTML instructions",
        example="Оновлені інструкції: додано практичне завдання."
    )
    start_at: Optional[datetime] = Field(
        None,
        description="Start datetime (UTC)",
        example="2026-11-15T09:00:00Z"
    )
    end_at: Optional[datetime] = Field(
        None,
        description="End datetime (UTC)",
        example="2028-02-20T18:00:00Z"
    )
    duration_minutes: Optional[int] = Field(
        None,
        description="Duration of the exam in minutes",
        example=120
    )
    max_attempts: Optional[conint(ge=1, le=10)] = Field( # type: ignore
        None,
        description="Max attempts per user",
        example=2
    )
    pass_threshold: Optional[conint(ge=0, le=100)] = Field( # type: ignore
        None,
        description="Passing threshold in percent",
        example=80
    )
    published: Optional[bool] = Field(None, description="Publish exam (true/false)")

    # Attach validators to this model
    _validate_start_at_not_in_past = validator("start_at", allow_reuse=True)(datetime_must_not_be_in_past)
    _validate_end_at_not_in_past = validator("end_at", allow_reuse=True)(datetime_must_not_be_in_past)
    _validate_dates = validator("end_at", allow_reuse=True)(end_at_must_be_after_start_at)

class Exam(BaseModel):
    id: UUID = Field(
        ...,
        example="a1b2c3d4-e5f6-7890-1234-567890abcdef"
    )
    title: str = Field(
        ...,
        example=EXAMPLE_TITLE,
    )
    instructions: Optional[str] = Field(
        None,
        example=DEFAULT_INSTRUCTIONS
    )
    start_at: datetime = Field(
        ...,
        example="2024-10-08T10:00:00Z"
    )
    end_at: datetime = Field(
        ...,
        example=DEFAULT_END_AT_EXAMPLE
    )
    duration_minutes: int = Field(
        ...,
        example=60,
        description="Duration of the exam in minutes"
    )
    max_attempts: int = Field(
        ...,
        example=3
    )
    pass_threshold: int = Field(
        ...,
        example=75
    )
    owner_id: UUID = Field(
        ...,
        example="c7a1c7e2-4a2c-4b6e-8e7f-9d3c5f2b1a8e"
    )
    published: bool = Field(False, description="Whether exam is published")
    question_count: int = Field(
        0,
        description="Number of available questions",
        example=20
    )

    model_config = {"from_attributes": True}

# Схема для іспиту з питаннями (для редагування)
from src.api.schemas.questions import QuestionSchema

class ExamWithQuestions(Exam):
    questions: List[QuestionSchema] = Field(
        default_factory=list,
        description="List of exam questions with options"
    )
    
    model_config = {"from_attributes": True}

class ExamsPage(BaseModel):
    items: List[Exam] = Field(
        ...,
        example=[
            {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": EXAMPLE_TITLE,
                "instructions": DEFAULT_INSTRUCTIONS,
                "start_at": "2024-10-08T10:00:00Z",
                "end_at": DEFAULT_END_AT_EXAMPLE,
                "max_attempts": 3,
                "duration_minutes": 120,
                "pass_threshold": 75,
                "owner_id": "c7a1c7e2-4a2c-4b6e-8e7f-9d3c5f2b1a8e",
                "question_count": 20
            }
        ]
    )
    total: int = Field(
        ...,
        example=1
    )

    model_config = {"from_attributes": True}

class ExamsResponse(BaseModel):
    future: List[ExamSchema] # type: ignore
    completed: List[ExamSchema] # type: ignore

class ExamInList(BaseModel):
    id: UUID
    title: str
    status: ExamStatusEnum
    questions_count: int = Field(0)
    students_completed: str
    average_grade: Optional[float] = None
    pending_reviews: int = Field(0)

    class Config:
        from_attributes = True

class CourseExamsPage(BaseModel):
    course_id: UUID
    course_name: str
    exams: List[ExamInList]

class ExamStatistics(BaseModel):
    exam_id: UUID
    min_score: Optional[float]
    max_score: Optional[float]
    median_score: Optional[float]
    total_students: int
