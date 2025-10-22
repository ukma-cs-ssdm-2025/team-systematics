from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from src.api.schemas.attempts import AttemptStartRequest, Attempt
from src.models.attempts import AttemptStatus
from src.api.errors.app_errors import NotFoundError
from datetime import datetime, timezone

class ExamsService:
    def list(self, db: Session, user_id: UUID, limit: int, offset: int):
        """
        Завжди повертає персоналізований список іспитів для користувача.
        """
        repo = ExamsRepository(db)
        items_with_status, _ = repo.list(user_id=user_id, limit=limit, offset=offset)
        
        now = datetime.now(timezone.utc)
        future_or_active = []
        completed_by_user = []

        for exam_model, attempt_status in items_with_status:
            exam_schema = Exam.model_validate(exam_model)

            if attempt_status in (AttemptStatus.submitted, AttemptStatus.completed):
                completed_by_user.append(exam_schema)
            
            elif exam_schema.end_at > now:
                future_or_active.append(exam_schema)

        return {"future": future_or_active, "completed": completed_by_user}

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