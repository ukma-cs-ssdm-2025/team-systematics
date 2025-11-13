from sqlalchemy.orm import Session, load_only, joinedload
from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Path
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt as AttemptSchema, AttemptResultResponse, AnswerScoreUpdate
from src.api.schemas.exam_review import ExamAttemptReviewResponse
from src.api.services.attempts_service import AttemptsService
from src.api.services.exam_review_service import ExamReviewService
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.models.attempts import Answer as AnswerModel, Attempt as AttemptModel
from src.models.exams import QuestionType, Question
from src.utils.largest_remainder import distribute_largest_remainder
from src.utils.auth import get_current_user_with_role
from src.models.users import User
from .versioning import require_api_version
from src.api.database import get_db
from src.api.dependencies import get_current_user
from typing import List, Optional
from src.api.schemas.plagiarism import (
    PlagiarismCheckSummary, 
    PlagiarismComparisonResponse,
    FlaggedAnswerResponse,
    AnswerComparisonResponse
)

class AttemptsController:
    def __init__(self, service: AttemptsService, review_service: ExamReviewService) -> None:
        self.service = service
        self.review_service = review_service
        self.router = APIRouter(prefix="/attempts", tags=["Attempts"], dependencies=[Depends(require_api_version)])
        self._setup_routes()

    def _calculate_max_points(self, db: Session, attempt_id: UUID, question_id: UUID) -> float:
        """Calculate max points for a question based on exam weights."""
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
        return final_points_map.get(question_id, 0)

    def _setup_routes(self):
        """Setup all route handlers for the attempts router."""
    
        # Окремий метод для реєстрації роутів
        self._register_flagged_answers_route()

    # Окремий метод для реєстрації роутів
    def _register_flagged_answers_route(self):
        @self.router.get(
            "/flagged-answers",
            response_model=List[FlaggedAnswerResponse],
            summary="Отримати список позначених відповідей (лише викладач)",
        )
        async def list_flagged_answers(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            # Перевірка ролі виконується всередині сервісу
            return self.service.list_flagged_answers(
                db=db,
                current_user=current_user,
            )
        
        @self.router.post("/{attempt_id}/answers", response_model=Answer, status_code=status.HTTP_201_CREATED, summary="Save or update an answer")
        async def add_answer(payload: AnswerUpsert, attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.add_answer(db, attempt_id, payload)

        @self.router.post("/{attempt_id}/submit", response_model=AttemptSchema, summary="Submit attempt")
        async def submit(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.submit(db, attempt_id)

        @self.router.get("/{attempt_id}", summary="Get attempt details for UI")
        async def get_attempt_details(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.get_attempt_details(db, attempt_id)

        @self.router.get("/{attempt_id}/results", response_model=AttemptResultResponse, summary="Send exam results")
        async def read_attempt_result(
            attempt_id: UUID,
            db: Session = Depends(get_db),
        ):
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
            max_points = self._calculate_max_points(db, attempt_id, question.id)
            
            try:
                return self.service.update_answer_score(
                    db, attempt_id, answer.id, payload, max_points
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        @self.router.get(
            "/exam/{exam_id}/plagiarism-checks",
            response_model=List[PlagiarismCheckSummary],
            summary="Список результатів перевірки на плагіат для іспиту (лише викладач)",
        )
        async def list_plagiarism_checks(
            exam_id: UUID,
            max_uniqueness: Optional[float] = None,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            return self.service.get_exam_plagiarism_checks(
                db=db,
                exam_id=exam_id,
                current_user=current_user,
                max_uniqueness=max_uniqueness,
            )

        @self.router.get(
            "/{attempt_id}/plagiarism/compare/{other_attempt_id}",
            response_model=PlagiarismComparisonResponse,
            summary="Порівняння текстів двох спроб (лише викладач)",
        )
        async def compare_attempts(
            attempt_id: UUID,
            other_attempt_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            return self.service.get_attempts_comparison(
                db=db,
                base_attempt_id=attempt_id,
                other_attempt_id=other_attempt_id,
                current_user=current_user,
            )
        
        @self.router.post(
            "/answers/{answer_id}/flag",
            response_model=FlaggedAnswerResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Позначити відповідь для перевірки на плагіат (лише викладач)",
        )
        async def flag_answer(
            answer_id: UUID = Path(..., description="ID відповіді"),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для вчителів"
                )
            return self.service.flag_answer_for_plagiarism_check(
                db=db,
                answer_id=answer_id,
                current_user=current_user,
            )
        
        @self.router.delete(
            "/answers/{answer_id}/flag",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Зняти позначення з відповіді (лише викладач)",
        )
        async def unflag_answer(
            answer_id: UUID = Path(..., description="ID відповіді"),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для вчителів"
                )
            self.service.unflag_answer(
                db=db,
                answer_id=answer_id,
                current_user=current_user,
            )
            return None
        
        @self.router.post(
            "/answers/{answer1_id}/compare/{answer2_id}",
            response_model=AnswerComparisonResponse,
            summary="Порівняти дві відповіді на плагіат (лише викладач)",
        )
        async def compare_answers(
            answer1_id: UUID = Path(..., description="ID першої відповіді"),
            answer2_id: UUID = Path(..., description="ID другої відповіді"),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для вчителів"
                )
            return self.service.compare_two_answers(
                db=db,
                answer1_id=answer1_id,
                answer2_id=answer2_id,
                current_user=current_user,
            )
        
        @self.router.get(
            "/{attempt_id}/questions/{question_id}/answer-id",
            summary="Отримати ID відповіді за attempt_id та question_id (лише викладач)",
        )
        async def get_answer_id(
            attempt_id: UUID = Path(..., description="ID спроби"),
            question_id: UUID = Path(..., description="ID питання"),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для вчителів"
                )
            
            # Перевіряємо, чи існує спроба та питання
            attempt = db.query(AttemptModel).filter(AttemptModel.id == attempt_id).first()
            if not attempt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Спроба не знайдена"
                )
            
            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Питання не знайдене"
                )
            
            # Перевіряємо, чи питання належить до цього іспиту
            if question.exam_id != attempt.exam_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Питання не належить до цього іспиту"
                )
            
            # Шукаємо відповідь
            answer = (
                db.query(AnswerModel)
                .filter(
                    AnswerModel.attempt_id == attempt_id,
                    AnswerModel.question_id == question_id
                )
                .first()
            )
            
            # Якщо відповіді немає, але це long_answer питання, можна створити порожню відповідь
            if not answer and question.question_type == QuestionType.long_answer:
                # Створюємо порожню відповідь для long_answer питань
                from datetime import datetime, timezone
                answer = AnswerModel(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    answer_text="",  # Порожня відповідь
                    saved_at=datetime.now(timezone.utc)
                )
                db.add(answer)
                db.commit()
                db.refresh(answer)
            
            if not answer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Відповідь не знайдена"
                )
            return {"answer_id": str(answer.id)}
