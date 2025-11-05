from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, conint, constr, validator

# --- Constants for Descriptions ---
DURATION_MINUTES_DESC = "Duration of the exam in minutes"
EXAM_TITLE_DESC = "Exam title"
INSTRUCTIONS_DESC = "Markdown/HTML instructions"
START_AT_DESC = "Start datetime (UTC)"
END_AT_DESC = "End datetime (UTC)"
MAX_ATTEMPTS_DESC = "Max attempts per user"
PASS_THRESHOLD_DESC = "Passing threshold in percent"
OWNER_ID_DESC = "Instructor user id"
QUESTION_COUNT_DESC = "Number of available questions"

# --- Constants for Example Values ---
EXAM_ID_EXAMPLE = UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")
OWNER_ID_EXAMPLE = UUID("c7a1c7e2-4a2c-4b6e-8e7f-9d3c5f2b1a8e")

EXAM_TITLE_EXAMPLE = "Вступ до Docker"
EXAM_INSTRUCTIONS_EXAMPLE = "Іспит складається з 20 теоретичних питань."

START_AT_CREATE_EXAMPLE = "2026-10-08T10:00:00Z"
END_AT_CREATE_EXAMPLE = "2027-10-08T10:00:00Z"

START_AT_EXAMPLE = "2024-10-08T10:00:00Z"
END_AT_EXAMPLE = "2027-10-08T10:00:00Z"

# --- Constants for Default Values & Examples ---
DURATION_MINUTES_DEFAULT = 60
DURATION_MINUTES_EXAMPLE = 120

MAX_ATTEMPTS_DEFAULT = 1
MAX_ATTEMPTS_EXAMPLE = 3

PASS_THRESHOLD_DEFAULT = 60
PASS_THRESHOLD_EXAMPLE = 75

QUESTION_COUNT_DEFAULT = 0
QUESTION_COUNT_EXAMPLE = 20


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
    title: constr(min_length=3, max_length=100) = Field(
        ...,
        description=EXAM_TITLE_DESC,
        example=EXAM_TITLE_EXAMPLE
    )
    instructions: Optional[constr(max_length=2000)] = Field(
        None,
        description=INSTRUCTIONS_DESC,
        example=EXAM_INSTRUCTIONS_EXAMPLE
    )
    start_at: datetime = Field(
        ...,
        example=START_AT_CREATE_EXAMPLE,
        description=START_AT_DESC
    )
    end_at: datetime = Field(
        ...,
        example=END_AT_CREATE_EXAMPLE,
        description=END_AT_DESC
    )
    duration_minutes: int = Field(
        DURATION_MINUTES_DEFAULT,
        description=DURATION_MINUTES_DESC,
        example=DURATION_MINUTES_EXAMPLE
    )
    max_attempts: conint(ge=1, le=10) = Field(
        MAX_ATTEMPTS_DEFAULT,
        description=MAX_ATTEMPTS_DESC,
        example=MAX_ATTEMPTS_EXAMPLE
    )
    pass_threshold: conint(ge=0, le=100) = Field(
        PASS_THRESHOLD_DEFAULT,
        description=PASS_THRESHOLD_DESC,
        example=PASS_THRESHOLD_EXAMPLE
    )
    owner_id: UUID = Field(
        ...,
        description=OWNER_ID_DESC,
        example=OWNER_ID_EXAMPLE
    )

    _validate_dates = validator("end_at", allow_reuse=True)(end_at_must_be_after_start_at)


class ExamUpdate(BaseModel):
    title: Optional[constr(min_length=3, max_length=100)] = Field(
        None,
        description=EXAM_TITLE_DESC,
        example="Docker: Просунутий рівень"
    )
    instructions: Optional[constr(max_length=2000)] = Field(
        None,
        description=INSTRUCTIONS_DESC,
        example="Оновлені інструкції: додано практичне завдання."
    )
    start_at: Optional[datetime] = Field(
        None,
        description=START_AT_DESC,
        example="2026-11-15T09:00:00Z"
    )
    end_at: Optional[datetime] = Field(
        None,
        description=END_AT_DESC,
        example="2028-02-20T18:00:00Z"
    )
    duration_minutes: Optional[int] = Field(
        None,
        description=DURATION_MINUTES_DESC,
        example=DURATION_MINUTES_EXAMPLE
    )
    max_attempts: Optional[conint(ge=1, le=10)] = Field(
        None,
        description=MAX_ATTEMPTS_DESC,
        example=2
    )
    pass_threshold: Optional[conint(ge=0, le=100)] = Field(
        None,
        description=PASS_THRESHOLD_DESC,
        example=80
    )

    # Attach the same validator to this model
    _validate_dates = validator("end_at", allow_reuse=True)(end_at_must_be_after_start_at)

class Exam(BaseModel):
    id: UUID = Field(
        ...,
        example=EXAM_ID_EXAMPLE
    )
    title: str = Field(
        ...,
        example=EXAM_TITLE_EXAMPLE
    )
    instructions: Optional[str] = Field(
        None,
        example=EXAM_INSTRUCTIONS_EXAMPLE
    )
    start_at: datetime = Field(
        ...,
        example=START_AT_EXAMPLE
    )
    end_at: datetime = Field(
        ...,
        example=END_AT_EXAMPLE
    )
    duration_minutes: int = Field(
        ...,
        example=DURATION_MINUTES_DEFAULT,
        description=DURATION_MINUTES_DESC
    )
    max_attempts: int = Field(
        ...,
        example=MAX_ATTEMPTS_EXAMPLE
    )
    pass_threshold: int = Field(
        ...,
        example=PASS_THRESHOLD_EXAMPLE
    )
    owner_id: UUID = Field(
        ...,
        example=OWNER_ID_EXAMPLE
    )
    question_count: int = Field(
        QUESTION_COUNT_DEFAULT,
        description=QUESTION_COUNT_DESC,
        example=QUESTION_COUNT_EXAMPLE
    )

    model_config = {"from_attributes": True}

class ExamsPage(BaseModel):
    items: List[Exam] = Field(
        ...,
        example=[
            {
                "id": EXAM_ID_EXAMPLE,
                "title": EXAM_TITLE_EXAMPLE,
                "instructions": EXAM_INSTRUCTIONS_EXAMPLE,
                "start_at": START_AT_EXAMPLE,
                "end_at": END_AT_EXAMPLE,
                "max_attempts": MAX_ATTEMPTS_EXAMPLE,
                "duration_minutes": DURATION_MINUTES_EXAMPLE,
                "pass_threshold": PASS_THRESHOLD_EXAMPLE,
                "owner_id": OWNER_ID_EXAMPLE,
                "question_count": QUESTION_COUNT_EXAMPLE
            }
        ]
    )
    total: int = Field(
        ...,
        example=1
    )

    model_config = {"from_attributes": True}

class ExamsResponse(BaseModel):
    future: List[Exam]
    completed: List[Exam]