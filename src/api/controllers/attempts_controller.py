from sqlalchemy.orm import Session, load_only, joinedload
from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Path
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt, AttemptResultResponse, AnswerScoreUpdate
from src.api.schemas.exam_review import ExamAttemptReviewResponse
from src.api.services.attempts_service import AttemptsService
from src.api.services.exam_review_service import ExamReviewService
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.models.attempts import Answer as AnswerModel
from src.models.exams import QuestionType
from src.utils.largest_remainder import distribute_largest_remainder
from src.utils.auth import get_current_user_with_role
from src.models.users import User
from .versioning import require_api_version
from src.api.database import get_db

class AttemptsController:
    def __init__(self, service: AttemptsService, review_service: ExamReviewService) -> None:
        self.service = service
        self.review_service = review_service
        self.router = APIRouter(prefix="/attempts", tags=["Attempts"], dependencies=[Depends(require_api_version)])

        @self.router.post("/{attempt_id}/answers", response_model=Answer, status_code=status.HTTP_201_CREATED, summary="Save or update an answer")
        async def add_answer(payload: AnswerUpsert, attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.add_answer(db, attempt_id, payload)

        @self.router.post("/{attempt_id}/submit", response_model=Attempt, summary="Submit attempt")
        async def submit(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.submit(db, attempt_id)

        @self.router.get("/{attempt_id}", summary="Get attempt details for UI")
        async def get_attempt_details(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.get_attempt_details(db, attempt_id)

        @self.router.get("/{attempt_id}/results", response_model=AttemptResultResponse, summary="Send exam results")
        async def read_attempt_result(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.get_attempt_result(db, attempt_id=attempt_id)

        @self.router.get("/{attempt_id}/review", response_model=ExamAttemptReviewResponse,
            summary="Отримати детальний огляд спроби іспиту")
        async def get_exam_attempt_review(
            attempt_id: UUID,
            db: Session = Depends(get_db),
        ):
            return self.review_service.get_attempt_review(attempt_id=attempt_id, db=db)

        @self.router.patch("/{attempt_id}/questions/{question_id}/score", 
            response_model=Answer, 
            status_code=status.HTTP_200_OK,
            summary="Оновити оцінку за відповідь на long_answer питання (тільки для вчителя)")
        async def update_answer_score(
            attempt_id: UUID = Path(..., description="ID спроби"),
            question_id: UUID = Path(..., description="ID питання"),
            payload: AnswerScoreUpdate = ...,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            # Перевірка ролі вчителя
            # Використовуємо lower() для безпечної перевірки, оскільки роль може бути в різних регістрах
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Цей функціонал доступний лише для вчителів. Ваша роль: {current_user.role}"
                )
            
            # Знаходимо answer за question_id та attempt_id
            # Також завантажуємо question для перевірки типу
            answer = db.query(AnswerModel).options(
                joinedload(AnswerModel.question)
            ).filter(
                AnswerModel.question_id == question_id,
                AnswerModel.attempt_id == attempt_id
            ).first()
            
            if not answer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Answer not found"
                )
            
            # Отримуємо question для перевірки типу та розрахунку max_points
            question = answer.question
            if question.question_type != QuestionType.long_answer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Цей endpoint призначений тільки для long_answer питань"
                )
            
            # Розраховуємо max_points (final_points для цього питання)
            attempts_repo = AttemptsRepository(db)
            weights_repo = WeightsRepository(db)
            attempt = attempts_repo.get_attempt(attempt_id)
            
            if not attempt or not attempt.exam:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attempt not found"
                )
            
            weights_map = weights_repo.get_all_weights()
            total_exam_weight = sum(
                weights_map.get(q.question_type, 1) for q in attempt.exam.questions
            )
            
            if total_exam_weight == 0:
                points_per_weight_unit = 0.0
            else:
                points_per_weight_unit = 100.0 / total_exam_weight
            
            true_points_map = {
                q.id: weights_map.get(q.question_type, 1) * points_per_weight_unit
                for q in attempt.exam.questions
            }
            
            final_points_map = distribute_largest_remainder(true_points_map, target_total=100)
            max_points = final_points_map.get(question.id, 0)
            
            try:
                return self.service.update_answer_score(
                    db, attempt_id, answer.id, payload, max_points
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )