from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from src.models.attempts import AttemptStatus

class AttemptInJournal(BaseModel):
    id: UUID
    attempt_number: int
    grade: Optional[float] = Field(None, alias="earned_points")
    time_spent_minutes: Optional[int]
    status: AttemptStatus

    class Config:
        from_attributes = True
        populate_by_name = True

class StudentInJournal(BaseModel):
    id: UUID
    full_name: str
    attempts_count: int
    max_grade: Optional[float] = None
    overall_status: AttemptStatus | str
    attempts: List[AttemptInJournal]

class ExamJournalResponse(BaseModel):
    exam_id: UUID
    exam_name: str
    max_attempts: int
    students: List[StudentInJournal]