from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt
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