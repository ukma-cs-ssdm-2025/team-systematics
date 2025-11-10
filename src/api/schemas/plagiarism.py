from __future__ import annotations

from typing import List, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class PlagiarismMatch(BaseModel):
    """
    Один збіг з іншою спробою.
    """
    other_attempt_id: UUID = Field(..., description="ID іншої спроби, з якою знайдено схожість")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Косинусна подібність у діапазоні [0.0, 1.0]",
    )
    match_type: Literal["exact", "candidate", "paraphrase"] = Field(
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
    status: Literal["ok", "suspicious", "high_risk"] = Field(
        ...,
        description="Підсумковий статус: ок / підозріло / високий ризик плагіату",
    )
    matches: List[PlagiarismMatch] = Field(
        default_factory=list,
        description="Список знайдених збігів з іншими роботами",
    )
