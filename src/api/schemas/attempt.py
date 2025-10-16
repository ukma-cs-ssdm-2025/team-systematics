from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# --- Схеми для Відповідей ---

class AnswerBase(BaseModel):
    question_id: UUID
    value: dict # JSONB поле для збереження тексту, ID опцій, тощо

class AnswerCreate(AnswerBase):
    pass

class AnswerSchema(AnswerBase):
    id: UUID
    attempt_id: UUID

    class Config:
        orm_mode = True

# --- Схеми для Спроб ---

class AttemptBase(BaseModel):
    exam_id: UUID
    user_id: UUID

class AttemptCreate(AttemptBase):
    pass

class AttemptSchema(AttemptBase):
    id: UUID
    status: str
    started_at: datetime
    due_at: datetime
    submitted_at: Optional[datetime] = None
    score_percent: Optional[int] = None
    answers: List[AnswerSchema] = []

    class Config:
        orm_mode = True