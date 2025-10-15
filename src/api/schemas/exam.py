from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ExamSchema(BaseModel):
    id: UUID
    title: str
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    max_attempts: int
    pass_threshold: int
    question_count: int

    class Config:
        orm_mode = True

class ExamsResponse(BaseModel):
    future: List[ExamSchema]
    completed: List[ExamSchema]