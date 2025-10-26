from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Dict, Any, Annotated
from uuid import UUID

# --- Моделі для варіантів відповідей ---

class SingleChoiceOption(BaseModel):
    id: str
    text: str
    is_correct: bool
    is_selected: bool

class MultiChoiceOption(SingleChoiceOption):
    earned_points_per_option: float

# --- Моделі для типу "Matching" ---

class MatchingPrompt(BaseModel):
    id: str
    text: str
    student_match_id: Optional[str]
    correct_match_id: str
    earned_points_per_match: float

class MatchingMatch(BaseModel):
    id: str
    text: str

class MatchingData(BaseModel):
    prompts: List[MatchingPrompt]
    matches: List[MatchingMatch]

# --- Базові моделі для різних типів питань ---
# Кожне питання має спільні поля

class BaseQuestionReview(BaseModel):
    id: str
    position: int
    title: str
    points: float
    earned_points: Optional[float] # 'null' для питань, що чекають на перевірку

# --- Конкретні типи питань ---

class SingleChoiceQuestionReview(BaseQuestionReview):
    question_type: Literal["single_choice"]
    options: List[SingleChoiceOption]

class MultiChoiceQuestionReview(BaseQuestionReview):
    question_type: Literal["multi_choice"]
    options: List[MultiChoiceOption]

class LongAnswerQuestionReview(BaseQuestionReview):
    question_type: Literal["long_answer"]
    student_answer_text: str

class ShortAnswerQuestionReview(BaseQuestionReview):
    question_type: Literal["short_answer"]
    student_answer_text: str
    correct_answer_text: Optional[str] # Може бути None, якщо ще не оцінено

class MatchingQuestionReview(BaseQuestionReview):
    question_type: Literal["matching"]
    matching_data: MatchingData

# --- Головна модель відповіді ---

# Використовуємо Union, щоб Pydantic сам визначив, яку модель питання використати
QuestionReview = Union[
    SingleChoiceQuestionReview,
    MultiChoiceQuestionReview,
    LongAnswerQuestionReview,
    ShortAnswerQuestionReview,
    MatchingQuestionReview
]

# Це головна модель, яку повертатиме API
class ExamAttemptReviewResponse(BaseModel):
    exam_title: str
    questions: List[
        Annotated[QuestionReview, Field(discriminator="question_type")]
    ]