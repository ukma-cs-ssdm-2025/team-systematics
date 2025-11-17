from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from fastapi import APIRouter, status, Depends, HTTPException, Path
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt as AttemptSchema, AttemptResultResponse, AnswerScoreUpdate, AddTimeRequest, ActiveAttemptInfo
from src.api.schemas.exam_review import ExamAttemptReviewResponse
from src.api.services.attempts_service import AttemptsService
from src.api.services.exam_review_service import ExamReviewService
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.models.attempts import Answer as AnswerModel, Attempt as AttemptModel
from src.models.exams import QuestionType, Question
from src.utils.largest_remainder import distribute_largest_remainder
from src.utils.auth import get_current_user_with_role, require_role
from src.models.users import User
from .versioning import require_api_version
from src.api.database import get_db
from typing import List, Optional
from src.api.schemas.plagiarism import (
    PlagiarismCheckSummary, 
    PlagiarismComparisonResponse,
    FlaggedAnswerResponse,
    AnswerComparisonResponse
)

TEACHER_ONLY_ACCESS = "Цей функціонал доступний лише для вчителів"
ATTEMPT_ID_DESCRIPTION = "ID спроби"

class AttemptsController:
    def __init__(self, service: AttemptsService, review_service: ExamReviewService) -> None:
        self.service = service
        self.review_service = review_service
        self.router = APIRouter(prefix="/attempts", tags=["Attempts"], dependencies=[Depends(require_api_version)])
        self._setup_routes()

    @staticmethod
    def _calculate_max_points(db: Session, attempt_id: UUID, question_id: UUID) -> float:
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

    @staticmethod
    def _require_teacher(current_user: User) -> None:
        user_role = str(current_user.role).lower().strip() if current_user.role else None
        if user_role != 'teacher':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=TEACHER_ONLY_ACCESS
            )

    # Extracted route handlers below. They are registered in `_register_flagged_answers_route`.
    def _list_flagged_answers(self, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        return self.service.list_flagged_answers(db=db, current_user=current_user)

    def _add_answer(self, payload: AnswerUpsert, attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: тільки студент може зберігати відповіді
        if current_user.role != 'student':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Тільки студенти можуть зберігати відповіді"
            )
        return self.service.add_answer(db, attempt_id, payload)

    def _submit(self, attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: тільки студент може завершувати спробу
        if current_user.role != 'student':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Тільки студенти можуть завершувати спроби"
            )
        return self.service.submit(db, attempt_id)

    def _get_attempt_details(self, attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: студент або вчитель можуть переглядати деталі спроби
        if current_user.role not in ['student', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ дозволений тільки студентам та вчителям"
            )
        return self.service.get_attempt_details(db, attempt_id)

    def _read_attempt_result(self, attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: студент або вчитель можуть переглядати результати
        if current_user.role not in ['student', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ дозволений тільки студентам та вчителям"
            )
        return self.service.get_attempt_result(db, attempt_id=attempt_id)

    def _get_exam_attempt_review(self, attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        return self.review_service.get_attempt_review(attempt_id=attempt_id, db=db, current_user=current_user)

    def _update_answer_score(self, attempt_id: UUID = Path(..., description=ATTEMPT_ID_DESCRIPTION),
                                   question_id: UUID = Path(..., description="ID питання"),
                                   payload: AnswerScoreUpdate = ...,
                                   db: Session = Depends(get_db),
                                   current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі вчителя
        self._require_teacher(current_user)

        # Знаходимо answer за question_id та attempt_id
        answer = db.query(AnswerModel).options(joinedload(AnswerModel.question)).filter(
            AnswerModel.question_id == question_id,
            AnswerModel.attempt_id == attempt_id
        ).first()
        if not answer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

        question = answer.question
        if question.question_type != QuestionType.long_answer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Цей endpoint призначений тільки для long_answer питань")

        max_points = self._calculate_max_points(db, attempt_id, question.id)
        try:
            return self.service.update_answer_score(db, attempt_id, answer.id, payload, max_points)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def _list_plagiarism_checks(self, exam_id: UUID, max_uniqueness: Optional[float] = None,
                                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: тільки вчитель може переглядати перевірки на плагіат
        self._require_teacher(current_user)
        return self.service.get_exam_plagiarism_checks(db=db, exam_id=exam_id, current_user=current_user, max_uniqueness=max_uniqueness)

    def _compare_attempts(self, attempt_id: UUID, other_attempt_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        # Перевірка ролі: тільки вчитель може порівнювати спроби
        self._require_teacher(current_user)
        return self.service.get_attempts_comparison(db=db, base_attempt_id=attempt_id, other_attempt_id=other_attempt_id, current_user=current_user)

    def _flag_answer(self, answer_id: UUID = Path(..., description="ID відповіді"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        self._require_teacher(current_user)
        return self.service.flag_answer_for_plagiarism_check(db=db, answer_id=answer_id, current_user=current_user)

    def _unflag_answer(self, answer_id: UUID = Path(..., description="ID відповіді"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        self._require_teacher(current_user)
        self.service.unflag_answer(db=db, answer_id=answer_id, current_user=current_user)

    def _compare_answers(self, answer1_id: UUID = Path(..., description="ID першої відповіді"), answer2_id: UUID = Path(..., description="ID другої відповіді"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        self._require_teacher(current_user)
        return self.service.compare_two_answers(db=db, answer1_id=answer1_id, answer2_id=answer2_id, current_user=current_user)

    def _get_answer_id(self, attempt_id: UUID = Path(..., description=ATTEMPT_ID_DESCRIPTION), question_id: UUID = Path(..., description="ID питання"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
        self._require_teacher(current_user)

        attempt = db.query(AttemptModel).filter(AttemptModel.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Спроба не знайдена")

        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Питання не знайдене")

        if question.exam_id != attempt.exam_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Питання не належить до цього іспиту")

        answer = db.query(AnswerModel).filter(AnswerModel.attempt_id == attempt_id, AnswerModel.question_id == question_id).first()
        if not answer and question.question_type == QuestionType.long_answer:
            from datetime import datetime, timezone
            answer = AnswerModel(attempt_id=attempt_id, question_id=question_id, answer_text="", saved_at=datetime.now(timezone.utc))
            db.add(answer)
            db.commit()
            db.refresh(answer)

        if not answer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відповідь не знайдена")
        return {"answer_id": str(answer.id)}

    def _get_active_attempts(self, exam_id: UUID = Path(..., description="ID іспиту"), db: Session = Depends(get_db)):
        return self.service.get_active_attempts_for_exam(db=db, exam_id=exam_id)

    def _get_completed_attempts(self, exam_id: UUID = Path(..., description="ID іспиту"), db: Session = Depends(get_db)):
        return self.service.get_completed_attempts_for_exam(db=db, exam_id=exam_id)

    def _add_time_to_attempt(self, attempt_id: UUID = Path(..., description=ATTEMPT_ID_DESCRIPTION), payload: AddTimeRequest = ..., db: Session = Depends(get_db)):
        return self.service.add_time_to_attempt(db=db, attempt_id=attempt_id, payload=payload)

    # Окремий метод для реєстрації роутів
    def _register_flagged_answers_route(self):
        # Register route handlers using extracted methods
        self.router.add_api_route(
            "/flagged-answers",
            endpoint=self._list_flagged_answers,
            response_model=List[FlaggedAnswerResponse],
            methods=["GET"],
            summary="Отримати список позначених відповідей (лише викладач)",
        )

        # Роути для exam мають бути перед роутами з {attempt_id}, щоб уникнути конфліктів
        self.router.add_api_route(
            "/exam/{exam_id}/active-attempts",
            endpoint=self._get_active_attempts,
            response_model=List[ActiveAttemptInfo],
            methods=["GET"],
            summary="Отримати список активних спроб для іспиту (тільки для наглядача)",
            dependencies=[Depends(require_role('supervisor'))],
        )

        self.router.add_api_route(
            "/exam/{exam_id}/completed-attempts",
            endpoint=self._get_completed_attempts,
            methods=["GET"],
            summary="Отримати список завершених спроб для іспиту (тільки для наглядача)",
            dependencies=[Depends(require_role('supervisor'))],
        )

        self.router.add_api_route(
            "/{attempt_id}/answers",
            endpoint=self._add_answer,
            response_model=Answer,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="Save or update an answer",
        )

        self.router.add_api_route(
            "/{attempt_id}/submit",
            endpoint=self._submit,
            response_model=AttemptSchema,
            methods=["POST"],
            summary="Submit attempt",
        )

        self.router.add_api_route(
            "/{attempt_id}",
            endpoint=self._get_attempt_details,
            methods=["GET"],
            summary="Get attempt details for UI",
        )

        self.router.add_api_route(
            "/{attempt_id}/results",
            endpoint=self._read_attempt_result,
            response_model=AttemptResultResponse,
            methods=["GET"],
            summary="Send exam results",
        )

        self.router.add_api_route(
            "/{attempt_id}/review",
            endpoint=self._get_exam_attempt_review,
            response_model=ExamAttemptReviewResponse,
            methods=["GET"],
            summary="Отримати детальний огляд спроби іспиту",
        )

        self.router.add_api_route(
            "/{attempt_id}/questions/{question_id}/score",
            endpoint=self._update_answer_score,
            response_model=Answer,
            methods=["PATCH"],
            status_code=status.HTTP_200_OK,
            summary="Оновити оцінку за відповідь на long_answer питання (тільки для вчителя)",
        )

        self.router.add_api_route(
            "/exam/{exam_id}/plagiarism-checks",
            endpoint=self._list_plagiarism_checks,
            response_model=List[PlagiarismCheckSummary],
            methods=["GET"],
            summary="Список результатів перевірки на плагіат для іспиту (лише викладач)",
        )

        self.router.add_api_route(
            "/{attempt_id}/plagiarism/compare/{other_attempt_id}",
            endpoint=self._compare_attempts,
            response_model=PlagiarismComparisonResponse,
            methods=["GET"],
            summary="Порівняння текстів двох спроб (лише викладач)",
        )

        self.router.add_api_route(
            "/answers/{answer_id}/flag",
            endpoint=self._flag_answer,
            response_model=FlaggedAnswerResponse,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="Позначити відповідь для перевірки на плагіат (лише викладач)",
        )

        self.router.add_api_route(
            "/answers/{answer_id}/flag",
            endpoint=self._unflag_answer,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Зняти позначення з відповіді (лише викладач)",
        )

        self.router.add_api_route(
            "/answers/{answer1_id}/compare/{answer2_id}",
            endpoint=self._compare_answers,
            response_model=AnswerComparisonResponse,
            methods=["POST"],
            summary="Порівняти дві відповіді на плагіат (лише викладач)",
        )

        self.router.add_api_route(
            "/{attempt_id}/questions/{question_id}/answer-id",
            endpoint=self._get_answer_id,
            methods=["GET"],
            summary="Отримати ID відповіді за attempt_id та question_id (лише викладач)",
        )

        self.router.add_api_route(
            "/{attempt_id}/add-time",
            endpoint=self._add_time_to_attempt,
            response_model=AttemptSchema,
            methods=["POST"],
            status_code=status.HTTP_200_OK,
            summary="Додати додатковий час до спроби студента (тільки для наглядача)",
            dependencies=[Depends(require_role('supervisor'))],
        )
