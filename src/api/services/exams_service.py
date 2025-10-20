from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from src.api.schemas.attempts import AttemptStartRequest, Attempt
from src.api.errors.app_errors import NotFoundError
from datetime import datetime, timezone

class ExamsService:
    def list(self, db: Session, limit: int, offset: int):
        repo = ExamsRepository(db)
        items, _ = repo.list(limit=limit, offset=offset)
        now = datetime.now(timezone.utc)
        future = []
        completed = []
        for item in items:
            exam = Exam.model_validate(item)
            if exam.end_at > now:
                future.append(exam)
            else:
                completed.append(exam)
        return {"future": future, "completed": completed}

    def get(self, db: Session, exam_id: UUID) -> Exam:
        repo = ExamsRepository(db)
        exam = repo.get(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
        return exam

    def create(self, db: Session, payload: ExamCreate) -> Exam:
        repo = ExamsRepository(db)
        return repo.create(payload)

    def update(self, db: Session, exam_id: UUID, patch: ExamUpdate) -> Exam:
        repo = ExamsRepository(db)
        updated = repo.update(exam_id, patch)
        if not updated:
            raise NotFoundError("Exam not found for update")
        return updated

    def delete(self, db: Session, exam_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete(exam_id)
        if not ok:
            raise NotFoundError("Exam not found for delete")

    def start_attempt(self, db: Session, exam_id: UUID, user_id: UUID) -> Attempt:
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
            
        attempts_repo = AttemptsRepository(db)
        return attempts_repo.create_attempt(
            exam_id=exam_id,
            user_id=user_id,
            duration_minutes=exam.duration_minutes
        )