from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from uuid import UUID
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.services.grading_service import GradingService
from src.api.schemas.attempts import (
    AnswerUpsert,
    Answer as AnswerSchema,
    Attempt as AttemptSchema,
    AttemptResultResponse
)
from src.models.attempts import Attempt, AttemptStatus, Answer
from src.models.exams import Exam, Question
from src.api.errors.app_errors import NotFoundError, ConflictError
from fastapi import HTTPException, status
from src.api.repositories.user_repository import UserRepository
from models.users import User

# Introduce Constant / Replace Magic Literal
ATTEMPT_NOT_FOUND_MSG = "Attempt not found"

class AttemptsService:
    def add_answer(self, db: Session, attempt_id: UUID, payload: AnswerUpsert) -> AnswerSchema:
        repo = AttemptsRepository(db)
        att = repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        if att.status != "in_progress":
            raise ConflictError("Attempt is locked or submitted")
        return repo.upsert_answer(attempt_id, payload)

    def submit(self, db: Session, attempt_id: UUID) -> AttemptSchema:
        """
        Завершує спробу, запускає повний процес оцінювання та зберігає результати.
        """
        repo = AttemptsRepository(db)
        grading_service = GradingService()

        attempt = db.query(Attempt).filter(Attempt.id == attempt_id).options(
            joinedload(Attempt.exam).selectinload(Exam.questions).selectinload(Question.options),
            joinedload(Attempt.exam).selectinload(Exam.questions).selectinload(Question.matching_options),
            selectinload(Attempt.answers).joinedload(Answer.question),
            selectinload(Attempt.answers).selectinload(Answer.selected_options)
        ).one_or_none()

        if not attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        if attempt.status != AttemptStatus.in_progress:
            raise ConflictError("Attempt is already submitted")

        repo.submit_attempt(attempt.id)

        # Викликаємо сервіс оцінювання, який поверне нам статистику
        grading_result = grading_service.calculate_score(db, attempt)
        
        # Обчислюємо загальну вагу іспиту для розрахунку фінальної оцінки
        total_exam_weight = db.query(func.sum(Question.points)).filter(
            Question.exam_id == attempt.exam_id
        ).scalar() or 0.0

        final_score = 0.0
        if total_exam_weight > 0:
            final_score = (grading_result.earned_weight / total_exam_weight) * 100

        final_score = min(100.0, final_score)

        attempt.correct_answers = grading_result.correct_count
        attempt.incorrect_answers = grading_result.incorrect_count
        attempt.pending_count = grading_result.pending_count
        attempt.earned_points = final_score

        if grading_result.pending_count > 0:
            attempt.status = AttemptStatus.submitted
        else:
            attempt.status = AttemptStatus.completed
            
        db.commit()
        db.refresh(attempt)
        
        return attempt

    def get_attempt_details(self, db: Session, attempt_id: UUID):
        repo = AttemptsRepository(db)
        att = repo.get_attempt_with_details(attempt_id)
        print(f"Спроба з функції отримання результатів: {att}")
        if not att:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        return att

    def get_attempt_result(self, db: Session, attempt_id: UUID) -> AttemptResultResponse:
        """
        Отримує вже обчислені результати спроби та форматує їх для відповіді API.
        """
        repo = AttemptsRepository(db)
        data = repo.get_attempt_result_raw(attempt_id)
        if not data:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)

        status = data["attempt_status"]
        if data["pending_count"] == 0 and status == "submitted":
            status = "completed"

        return AttemptResultResponse(
            exam_title=data["exam_title"],
            status=status,
            score=float(data["score"]),
            time_spent_seconds=data["time_spent_seconds"],
            total_questions=data["total_questions"],
            answers_given=data["answers_given"],
            correct_answers=data["correct_answers"],
            incorrect_answers=data["incorrect_answers"],
            pending_count=data["pending_count"]
        )

    def extend_attempt_time(
        self,
        db: Session,
        attempt_id: UUID,
        extra_minutes: int,
        current_user: User,
    ) -> AttemptSchema:
        """
        Додає додатковий час до дедлайну спроби іспиту.

        Доступно тільки для користувача з роллю 'supervisor'.
        Додатковий час можна додати лише для спроби студента в статусі 'in_progress'.
        """
        if extra_minutes <= 0:
            raise ConflictError("extra_minutes must be positive")

        user_repo = UserRepository(db)

        # 1. Перевіряємо, що поточний користувач – supervisor
        current_user_roles = user_repo.get_user_roles(current_user.id)
        if "supervisor" not in current_user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only supervisors can extend attempt time",
            )

        repo = AttemptsRepository(db)
        attempt = repo.get_attempt(attempt_id)
        if not attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)

        # 2. Переконуємось, що це спроба студента
        target_user_roles = user_repo.get_user_roles(attempt.user_id)
        if "student" not in target_user_roles:
            raise ConflictError("Time can be extended only for student attempts")

        # 3. Спроба має бути ще в процесі
        if attempt.status != AttemptStatus.in_progress:
            raise ConflictError("Attempt is not in progress")

        # 4. Подовжуємо дедлайн
        updated_attempt = repo.extend_attempt_time(attempt_id, extra_minutes)
        if not updated_attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)

        return updated_attempt
    