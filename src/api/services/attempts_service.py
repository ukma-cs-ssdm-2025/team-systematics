from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from uuid import UUID

from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.services.grading_service import GradingService
from src.api.schemas.attempts import (
    AnswerUpsert,
    Answer as AnswerSchema,
    Attempt as AttemptSchema,
    AttemptResultResponse,
)

from src.api.schemas.plagiarism import (
    PlagiarismReport,
    PlagiarismCheckSummary,
    PlagiarismComparisonResponse,
)

from src.models.attempts import Attempt, AttemptStatus, Answer
from src.models.exams import Exam, Question
from src.api.errors.app_errors import NotFoundError, ConflictError

from src.api.services.plagiarism_service import PlagiarismService
from src.api.repositories.plagiarism_repository import PlagiarismRepository
from src.models.users import User
from src.models.user_roles import UserRole
from src.models.paraphrase import ParaphraseModel

# Introduce Constant / Replace Magic Literal
ATTEMPT_NOT_FOUND_MSG = "Attempt not found"
TEACHER_ROLE_ID = 2

class AttemptsService:
    def __init__(self, plagiarism_service: Optional[PlagiarismService] = None) -> None:
        if plagiarism_service:
            self.plagiarism_service = plagiarism_service
        else:
            self.plagiarism_service = PlagiarismService(
                repo=PlagiarismRepository(),
                paraphrase_model=ParaphraseModel(),
            )

    def add_answer(
        self, db: Session, attempt_id: UUID, payload: AnswerUpsert
    ) -> AnswerSchema:
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

        # Автоматична перевірка на плагіат (тільки long_answer всередині сервісу)
        self.plagiarism_service.check_attempt(db, attempt)

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

    def get_attempt_result(
        self,
        db: Session,
        attempt_id: UUID,
        current_user: User,
    ) -> AttemptResultResponse:
        """
        Отримує вже обчислені результати спроби та форматує їх для відповіді API.
        Додає звіт про плагіат ТІЛЬКИ якщо поточний користувач є викладачем.
        """
        repo = AttemptsRepository(db)
        data = repo.get_attempt_result_raw(attempt_id)
        if not data:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)

        status = data["attempt_status"]
        if data["pending_count"] == 0 and status == "submitted":
            status = "completed"

        # За замовчуванням — без звіту про плагіат (для студентів)
        plagiarism_report: Optional[PlagiarismReport] = None

        # Якщо користувач — викладач, підтягуємо PlagiarismCheck
        if self._is_teacher(db, current_user):
            attempt: Optional[Attempt] = (
                db.query(Attempt)
                .options(joinedload(Attempt.plagiarism_check))
                .filter(Attempt.id == attempt_id)
                .one_or_none()
            )
            if attempt and attempt.plagiarism_check:
                plagiarism_report = self.plagiarism_service._to_report(
                    attempt.plagiarism_check
                )

        return AttemptResultResponse(
            exam_title=data["exam_title"],
            status=status,
            score=float(data["score"]),
            time_spent_seconds=data["time_spent_seconds"],
            total_questions=data["total_questions"],
            answers_given=data["answers_given"],
            correct_answers=data["correct_answers"],
            incorrect_answers=data["incorrect_answers"],
            pending_count=data["pending_count"],
            plagiarism_report=plagiarism_report,
        )

    def _is_teacher(self, db: Session, user: User) -> bool:
        """
        Перевіряємо, чи має користувач роль викладача через таблицю user_roles.
        TEACHER_ROLE_ID = 2.
        """
        return (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user.id,
                UserRole.role_id == TEACHER_ROLE_ID,
            )
            .first()
            is not None
        )
    
    def get_exam_plagiarism_checks(
        self,
        db: Session,
        exam_id: UUID,
        current_user: User,
        max_uniqueness: Optional[float] = None,
    ) -> List[PlagiarismCheckSummary]:
        """
        Список результатів перевірки на плагіат по іспиту (лише викладач).
        """
        if not self._is_teacher(db, current_user):
            # Якщо нема окремої ForbiddenError – використовуємо ConflictError
            raise ConflictError("Only teacher can view plagiarism checks")

        return self.plagiarism_service.list_exam_checks(
            db=db,
            exam_id=exam_id,
            max_uniqueness=max_uniqueness,
        )

    def get_attempts_comparison(
        self,
        db: Session,
        base_attempt_id: UUID,
        other_attempt_id: UUID,
        current_user: User,
    ) -> PlagiarismComparisonResponse:
        """
        Порівняння текстів двох спроб (лише викладач).
        """
        if not self._is_teacher(db, current_user):
            raise ConflictError("Only teacher can compare attempts for plagiarism")

        # Можна додатково перевірити, що обидві спроби існують:
        base = db.query(Attempt).filter(Attempt.id == base_attempt_id).one_or_none()
        other = db.query(Attempt).filter(Attempt.id == other_attempt_id).one_or_none()
        if not base or not other:
            raise NotFoundError("One or both attempts not found")

        return self.plagiarism_service.compare_attempts_texts(
            db=db,
            base_attempt_id=base_attempt_id,
            other_attempt_id=other_attempt_id,
        )
    
