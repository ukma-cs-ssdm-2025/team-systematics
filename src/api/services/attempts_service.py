from sqlalchemy.orm import Session, joinedload
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

class AttemptsService:
    def add_answer(self, db: Session, attempt_id: UUID, payload: AnswerUpsert) -> AnswerSchema:
        repo = AttemptsRepository(db)
        att = repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError("Attempt not found")
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
            selectinload(Attempt.answers).selectinload(Answer.options)
        ).one_or_none()

        if not attempt:
            raise NotFoundError("Attempt not found")
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
        
        attempt.correct_answers = grading_result.correct_count
        attempt.incorrect_answers = grading_result.incorrect_count
        attempt.pending_count = grading_result.pending_count
        attempt.score_percent = int(round(final_score))

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
        if not att:
            raise NotFoundError("Attempt not found")
        return att

    def get_attempt_result(self, db: Session, attempt_id: UUID) -> AttemptResultResponse:
        """
        Отримує вже обчислені результати спроби та форматує їх для відповіді API.
        """
        repo = AttemptsRepository(db)
        data = repo.get_attempt_result_raw(attempt_id)
        if not data:
            raise NotFoundError("Attempt not found")

        status = data["attempt_status"]
        if data["pending_count"] == 0 and status == "submitted":
            status = "completed"

        return AttemptResultResponse(
            exam_title=data["exam_title"],
            status=status,
            score_percent=float(data["score_percent"]),
            time_spent_seconds=data["time_spent_seconds"],
            total_questions=data["total_questions"],
            answers_given=data["answers_given"],
            correct_answers=data["correct_answers"],
            incorrect_answers=data["incorrect_answers"],
        )