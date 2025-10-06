from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, conint, constr

class ExamCreate(BaseModel):
    title: constr(min_length=3, max_length=100) = Field(..., description="Exam title")
    instructions: Optional[constr(max_length=2000)] = Field(None, description="Markdown/HTML instructions")
    start_at: Optional[datetime] = Field(None, description="Start datetime (UTC); null = available immediately")
    end_at: Optional[datetime] = Field(None, description="End datetime (UTC); null = no hard deadline")
    duration_minutes: conint(ge=5, le=600) = Field(..., description="Time limit per attempt in minutes")
    max_attempts: conint(ge=1, le=10) = Field(1, description="Max attempts per user")
    pass_threshold: conint(ge=0, le=100) = Field(60, description="Passing threshold in percent")
    owner_id: UUID = Field(..., description="Instructor user id")

class ExamUpdate(BaseModel):
    title: Optional[conint(strict=True) | constr(min_length=3, max_length=100)] = Field(None, description="Exam title")
    instructions: Optional[constr(max_length=2000)] = Field(None, description="Markdown/HTML instructions")
    start_at: Optional[datetime] = Field(None, description="Start datetime (UTC)")
    end_at: Optional[datetime] = Field(None, description="End datetime (UTC)")
    duration_minutes: Optional[conint(ge=5, le=600)] = Field(None, description="Time limit per attempt in minutes")
    max_attempts: Optional[conint(ge=1, le=10)] = Field(None, description="Max attempts per user")
    pass_threshold: Optional[conint(ge=0, le=100)] = Field(None, description="Passing threshold in percent")

class Exam(BaseModel):
    id: UUID
    title: str
    instructions: Optional[str] = None
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    max_attempts: int
    pass_threshold: int
    owner_id: UUID
    question_count: int = Field(0, description="Number of available questions")

class ExamsPage(BaseModel):
    items: List[Exam]
    total: int