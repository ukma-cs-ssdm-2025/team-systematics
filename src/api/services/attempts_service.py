from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt, AttemptResultResponse 
from src.api.errors.app_errors import NotFoundError, ConflictError

class AttemptsService:
    def add_answer(self, db: Session, attempt_id: UUID, payload: AnswerUpsert) -> Answer:
        repo = AttemptsRepository(db)
        att = repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError("Attempt not found")
        if att.status != "in_progress":
            raise ConflictError("Attempt is locked or submitted")
        return repo.upsert_answer(attempt_id, payload)

    def submit(self, db: Session, attempt_id: UUID) -> Attempt:
        repo = AttemptsRepository(db)
        att = repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError("Attempt not found")
        if att.status != "in_progress":
            raise ConflictError("Attempt is already submitted")
        return repo.submit_attempt(attempt_id)

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