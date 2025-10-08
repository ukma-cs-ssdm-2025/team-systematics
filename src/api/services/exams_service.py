from __future__ import annotations
from typing import List, Tuple
from uuid import UUID

from ..repositories.exams_repository import ExamsRepository
from ..repositories.attempts_repository import AttemptsRepository
from ..schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from ..schemas.attempts import AttemptStartRequest, Attempt
from ..errors.app_errors import NotFoundError

class ExamsService:
    def __init__(self, exams_repo: ExamsRepository, attempts_repo: AttemptsRepository) -> None:
        self.exams_repo = exams_repo
        self.attempts_repo = attempts_repo

    def list(self, limit: int, offset: int) -> ExamsPage:
        items, total = self.exams_repo.list(limit=limit, offset=offset)
        return ExamsPage(items=items, total=total)

    def get(self, exam_id: UUID) -> Exam:
        exam = self.exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError()
        return exam

    def create(self, payload: ExamCreate) -> Exam:
        return self.exams_repo.create(payload)

    def update(self, exam_id: UUID, patch: ExamUpdate) -> Exam:
        updated = self.exams_repo.update(exam_id, patch)
        if not updated:
            raise NotFoundError()
        return updated

    def delete(self, exam_id: UUID) -> None:
        ok = self.exams_repo.delete(exam_id)
        if not ok:
            raise NotFoundError()

    def start_attempt(self, exam_id: UUID, payload: AttemptStartRequest) -> Attempt:
        exam = self.exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError()
        return self.attempts_repo.create_attempt(exam_id=exam_id, user_id=payload.user_id, duration_minutes=exam.duration_minutes)