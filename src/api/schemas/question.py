from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from ..models.exam import QuestionType # Імпортуємо enum з моделі

# --- Схеми для Варіантів відповіді ---

class OptionBase(BaseModel):
    text: str
    is_correct: bool = False

class OptionCreate(OptionBase):
    pass

class OptionSchema(OptionBase):
    id: UUID
    question_id: UUID

    class Config:
        orm_mode = True

# --- Схеми для Питань ---

class QuestionBase(BaseModel):
    title: str
    question_type: QuestionType
    points: int = 1
    position: int = 0
    matching_data: Optional[dict] = None # Для питань на відповідність

class QuestionCreate(QuestionBase):
    options: List[OptionCreate] = []

class QuestionSchema(QuestionBase):
    id: UUID
    exam_id: UUID
    options: List[OptionSchema] = []

    class Config:
        orm_mode = True