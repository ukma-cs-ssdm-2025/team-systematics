from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, conint, constr, validator, PastDatetime, FutureDatetime

class ExamCreate(BaseModel):
    title: constr(min_length=3, max_length=100) = Field(
        ...,
        description="Exam title",
        example="Вступ до Docker"
    )
    instructions: Optional[constr(max_length=2000)] = Field(
        None,
        description="Markdown/HTML instructions",
        example="Іспит складається з 20 теоретичних питань."
    )
    start_at: PastDatetime = Field(
        ...,
        example="2024-10-08T10:00:00Z",
        description="Start datetime (UTC); must be in the past"
    )
    end_at: FutureDatetime = Field(
        ...,
        example="2027-10-08T10:00:00Z",
        description="End datetime (UTC); must be in the future"
    )
    max_attempts: conint(ge=1, le=10) = Field(
        1,
        description="Max attempts per user",
        example=3
    )
    pass_threshold: conint(ge=0, le=100) = Field(
        60,
        description="Passing threshold in percent",
        example=75
    )
    owner_id: UUID = Field(
        ...,
        description="Instructor user id",
        example="c7a1c7e2-4a2c-4b6e-8e7f-9d3c5f2b1a8e"
    )

class ExamUpdate(BaseModel):
    title: Optional[constr(min_length=3, max_length=100)] = Field(
        None,
        description="Exam title",
        example="Docker: Просунутий рівень"
    )
    instructions: Optional[constr(max_length=2000)] = Field(
        None,
        description="Markdown/HTML instructions",
        example="Оновлені інструкції: додано практичне завдання."
    )
    start_at: Optional[PastDatetime] = Field(
        None,
        description="Start datetime (UTC); must be in the past",
        example="2024-11-15T09:00:00Z"
    )
    end_at: Optional[FutureDatetime] = Field(
        None,
        description="End datetime (UTC); must be in the future",
        example="2028-02-20T18:00:00Z"
    )
    max_attempts: Optional[conint(ge=1, le=10)] = Field(
        None,
        description="Max attempts per user",
        example=2
    )
    pass_threshold: Optional[conint(ge=0, le=100)] = Field(
        None,
        description="Passing threshold in percent",
        example=80
    )

class Exam(BaseModel):
    id: UUID = Field(
        ...,
        example="a1b2c3d4-e5f6-7890-1234-567890abcdef"
    )
    title: str = Field(
        ...,
        example="Вступ до Docker"
    )
    instructions: Optional[str] = Field(
        None,
        example="Іспит складається з 20 теоретичних питань."
    )
    start_at: PastDatetime = Field(
        ...,
        example="2024-10-08T10:00:00Z"
    )
    end_at: FutureDatetime = Field(
        ...,
        example="2027-10-08T10:00:00Z"
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
    question_count: int = Field(
        0,
        description="Number of available questions",
        example=20
    )

    model_config = {"from_attributes": True}

class ExamsPage(BaseModel):
    items: List[Exam] = Field(
        ...,
        example=[
            {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "Вступ до Docker",
                "instructions": "Іспит складається з 20 теоретичних питань.",
                "start_at": "2024-10-08T10:00:00Z",
                "end_at": "2027-10-08T10:00:00Z",
                "max_attempts": 3,
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

@validator("end_at")
def end_at_must_be_after_start_at(cls, v, values, **kwargs):
    if "start_at" in values and values["start_at"] is not None and v <= values["start_at"]:
        raise ValueError("end_at must be after start_at")
    return v