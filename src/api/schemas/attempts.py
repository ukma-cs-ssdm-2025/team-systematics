from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, conint, constr, PastDatetime
from datetime import datetime
from src.api.schemas.plagiarism import PlagiarismReport

class Attempt(BaseModel):
    id: UUID
    exam_id: UUID
    user_id: UUID
    status: str = Field("in_progress", description="in_progress|submitted|expired")
    started_at: PastDatetime
    due_at: datetime
    submitted_at: Optional[PastDatetime] = None
    score_percent: Optional[conint(ge=0, le=100)] = None # type: ignore
    time_spent_seconds: Optional[int] = None

class AttemptStartRequest(BaseModel):
    user_id: UUID = Field(..., description="Student user id starting the attempt")

class AnswerUpsert(BaseModel):
    question_id: UUID = Field(..., description="Question id being answered")
    text: Optional[constr(max_length=5000)] = Field(None, description="Free text answer") # type: ignore
    selected_option_ids: Optional[List[UUID]] = Field(None, description="Selected option ids for MCQ")

class Answer(BaseModel):
    id: UUID
    attempt_id: UUID
    question_id: UUID
    text: Optional[str] = None
    selected_option_ids: Optional[List[UUID]] = None    
    saved_at: PastDatetime

class AnswerScoreUpdate(BaseModel):
    earned_points: float = Field(..., ge=0, description="Оцінка за питання (не може бути від'ємною)")

class AttemptResultResponse(BaseModel):
    exam_title: str
    status: str # in_progress | submitted | completed
    score: float
    time_spent_seconds: int
    total_questions: int
    answers_given: int
    correct_answers: int
    incorrect_answers: int
    pending_count: int
    plagiarism_report: Optional[PlagiarismReport] = None

class AddTimeRequest(BaseModel):
    additional_minutes: conint(ge=1, le=60) = Field(..., description="Кількість додаткових хвилин (1-60)") # type: ignore

class ActiveAttemptInfo(BaseModel):
    attempt_id: UUID
    user_id: UUID
    user_full_name: str
    started_at: datetime
    due_at: datetime
    remaining_minutes: int
    status: str