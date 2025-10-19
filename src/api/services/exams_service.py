from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from src.api.schemas.attempts import AttemptStartRequest, Attempt
from src.api.errors.app_errors import NotFoundError

class ExamsService:
    def list(self, db: Session, limit: int, offset: int) -> ExamsPage:
        repo = ExamsRepository(db)
        items, total = repo.list(limit=limit, offset=offset)
        pydantic_items = [Exam.model_validate(item) for item in items]
        return ExamsPage(items=pydantic_items, total=total)

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

    def start_attempt(self, db: Session, exam_id: UUID, payload: AttemptStartRequest) -> Attempt:
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
            
        attempts_repo = AttemptsRepository(db)
        return attempts_repo.create_attempt(
            exam_id=exam_id, 
            user_id=payload.user_id,
            duration_minutes=exam.duration_minutes
        )