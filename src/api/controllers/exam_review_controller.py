from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.database import get_db
from src.api.services.exam_review_service import ExamReviewService
from src.api.schemas.exam_reviews import ExamAttemptReviewResponse

router = APIRouter(
    prefix="/attempts",
    tags=["Exam Review"]
)

# Використовуємо Depends для ін'єкції сервісу
def get_exam_review_service() -> ExamReviewService:
    return ExamReviewService()

@router.get(
    "/{attempt_id}/review",
    response_model=ExamAttemptReviewResponse,
    summary="Отримати детальний огляд спроби іспиту"
)
async def get_exam_attempt_review(
    attempt_id: UUID = Path(..., description="ID спроби іспиту"),
    db: Session = Depends(get_db),
    review_service: ExamReviewService = Depends(get_exam_review_service)
):
    """
    Повертає повну структуру даних, необхідну для сторінки
    перегляду результатів іспиту студентом (або викладачем).
    
    Включає:
    - Назву іспиту
    - Список усіх питань
    - Варіанти відповідей
    - Відповіді студента
    - Правильні відповіді
    - Зароблені бали за кожне питання
    """
    review_data = review_service.get_attempt_review(attempt_id=attempt_id, db=db)
    
    # Pydantic автоматично валідує, що 'review_data'
    # відповідає схемі ExamAttemptReviewResponse
    return review_data