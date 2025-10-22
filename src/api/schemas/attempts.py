from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, conint, constr, PastDatetime
from datetime import datetime

class Attempt(BaseModel):
    id: UUID
    exam_id: UUID
    user_id: UUID
    status: str = Field("in_progress", description="in_progress|submitted|expired")
    started_at: PastDatetime
    due_at: datetime
    submitted_at: Optional[PastDatetime] = None
    score_percent: Optional[conint(ge=0, le=100)] = None

class AttemptStartRequest(BaseModel):
    user_id: UUID = Field(..., description="Student user id starting the attempt")

class AnswerUpsert(BaseModel):
    question_id: UUID = Field(..., description="Question id being answered")
    text: Optional[constr(max_length=5000)] = Field(None, description="Free text answer")
    selected_option_ids: Optional[List[UUID]] = Field(None, description="Selected option ids for MCQ")

class Answer(BaseModel):
    id: UUID
    attempt_id: UUID
    question_id: UUID
    text: Optional[str] = None
    selected_option_ids: Optional[List[UUID]] = None    
    saved_at: PastDatetime

class AttemptResultResponse(BaseModel):
    exam_title: str
    status: str # in_progress | submitted | completed
    score_percent: float # do not round
    time_spent_seconds: int
    total_questions: int
    answers_given: int
    correct_answers: int
    incorrect_answers: int