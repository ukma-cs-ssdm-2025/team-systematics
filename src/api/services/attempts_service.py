from __future__ import annotations
from uuid import UUID

from ..repositories.attempts_repository import AttemptsRepository
from ..schemas.attempts import AnswerUpsert, Answer, Attempt
from ..errors.app_errors import NotFoundError, ConflictError

class AttemptsService:
    def __init__(self, attempts_repo: AttemptsRepository) -> None:
        self.attempts_repo = attempts_repo

    def add_answer(self, attempt_id: UUID, payload: AnswerUpsert) -> Answer:
        att = self.attempts_repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError()
            
        if att.status != "in_progress":
            raise ConflictError()
            
        return self.attempts_repo.upsert_answer(
            attempt_id=attempt_id,
            question_id=payload.question_id,
            text=payload.text,
            selected_option_ids=payload.selected_option_ids,
        )

    def submit(self, attempt_id: UUID) -> Attempt:
        att = self.attempts_repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError()
            
        if att.status != "in_progress":
            raise ConflictError()
            
        updated = self.attempts_repo.submit_attempt(attempt_id)
        return updated