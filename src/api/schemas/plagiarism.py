from __future__ import annotations

from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel, Field

StatusLiteral = Literal["ok", "suspicious", "high_risk"]
MatchTypeLiteral = Literal["exact", "candidate", "paraphrase"]


class PlagiarismMatch(BaseModel):
    """
    Один збіг з іншою спробою.
    """
    other_attempt_id: UUID = Field(
        ...,
        description="ID іншої спроби, з якою знайдено схожість",
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Косинусна подібність у діапазоні [0.0, 1.0]",
    )
    match_type: MatchTypeLiteral = Field(
        ...,
        description="Тип збігу: exact (дослівно), paraphrase (перефраз), candidate (кандидат)",
    )


class PlagiarismReport(BaseModel):
    """
    Повний звіт по перевірці на плагіат для однієї спроби.
    """
    uniqueness_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Оцінка унікальності роботи в відсотках (0–100)",
    )
    status: StatusLiteral = Field(
        ...,
        description="Підсумковий статус: ok / suspicious / high_risk",
    )
    matches: List[PlagiarismMatch] = Field(
        default_factory=list,
        description="Список знайдених збігів з іншими роботами",
    )


class PlagiarismCheckSummary(BaseModel):
    """
    Коротка інформація для списку перевірених робіт (для фільтрації по <70%).
    """
    attempt_id: UUID = Field(..., description="ID спроби")
    student_id: UUID = Field(..., description="ID студента (user_id)")
    uniqueness_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Оцінка унікальності роботи (0–100)",
    )
    max_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Максимальна схожість з іншою роботою (0–1)",
    )
    status: StatusLiteral = Field(
        ...,
        description="ok / suspicious / high_risk",
    )


class PlagiarismComparisonResponse(BaseModel):
    """
    Відповідь для ендпоінту "порівняти дві роботи".
    """
    base_attempt_id: UUID = Field(..., description="Спроба, яку переглядає викладач")
    other_attempt_id: UUID = Field(..., description="Спроба, з якою порівнюємо")
    base_text: str = Field(..., description="Об'єднаний текст long_answer відповіді базової спроби")
    other_text: str = Field(..., description="Об'єднаний текст long_answer відповіді іншої спроби")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Підсумкова семантична схожість між текстами (0–1)",
    )


class FlaggedAnswerResponse(BaseModel):
    """Відповідь з інформацією про позначену відповідь"""
    answer_id: UUID = Field(..., description="ID відповіді")
    attempt_id: UUID = Field(..., description="ID спроби")
    question_id: UUID = Field(..., description="ID питання")
    student_name: str = Field(..., description="Повне ім'я студента")
    exam_title: str = Field(..., description="Назва іспиту")
    exam_id: UUID = Field(..., description="ID іспиту")
    answer_text: str = Field(..., description="Текст відповіді")
    flagged_at: str = Field(..., description="Дата позначення")


class AnswerComparisonResponse(BaseModel):
    """Відповідь для порівняння двох конкретних відповідей"""
    answer1_id: UUID = Field(..., description="ID першої відповіді")
    answer2_id: UUID = Field(..., description="ID другої відповіді")
    answer1_text: str = Field(..., description="Текст першої відповіді")
    answer2_text: str = Field(..., description="Текст другої відповіді")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Схожість між відповідями (0–1)",
    )
    student1_name: str = Field(..., description="Ім'я першого студента")
    student2_name: str = Field(..., description="Ім'я другого студента")
    exam_title: str = Field(..., description="Назва іспиту")
