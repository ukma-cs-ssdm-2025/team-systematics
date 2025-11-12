from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session

from src.api.repositories.exam_participants_repository import ExamParticipantsRepository
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.user_repository import UserRepository
from src.api.services.attempts_service import AttemptsService
from src.api.schemas.exam_participants import (
    ExamParticipantCreate,
    ExamParticipantResponse,
    ExamParticipantAttendanceUpdate,
)
from src.api.errors.app_errors import NotFoundError, ConflictError

from src.models.exam_participants import AttendanceStatusEnum
from src.models.exams import ExamStatusEnum

EXAM_NOT_FOUND = "Іспит не знайдено"
USER_NOT_FOUND = "Користувача не знайдено"
COURSE_ENROLL_REQUIRED = "Студент має бути зарахований на курс, щоб додатись до іспиту"
ALREADY_ACTIVE_SESSION = "Студент вже бере участь в іншій активній сесії іспиту"
NOT_A_PARTICIPANT = "Користувача не знайдено серед учасників іспиту"

class ExamParticipantsService:
    def list(self, db: Session, exam_id: UUID):
        repo = ExamParticipantsRepository(db)
        items = repo.list_active(exam_id)
        return [ExamParticipantResponse.model_validate(i) for i in items]

    def add(self, db: Session, exam_id: UUID, payload: ExamParticipantCreate):
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND)

        if exam.status == ExamStatusEnum.closed:
            raise ConflictError("Іспит зачинено для змін учасників")

        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(payload.user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)

        # без авто-енролу
        if not ExamParticipantsRepository(db).is_user_enrolled_to_course(payload.course_id, payload.user_id):
            raise ConflictError(COURSE_ENROLL_REQUIRED)

        # Заборона: студент уже в іншій активній сесії
        if ExamParticipantsRepository(db).has_active_attempt_in_other_exam(payload.user_id, exam_id):
            raise ConflictError(ALREADY_ACTIVE_SESSION)

        ep = ExamParticipantsRepository(db).add(exam_id, payload.user_id)
        return ExamParticipantResponse.model_validate(ep)

    def remove(self, db: Session, exam_id: UUID, user_id: UUID):
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND)

        repo = ExamParticipantsRepository(db)
        ep = repo.get(exam_id, user_id)
        if not ep or not ep.is_active:
            raise NotFoundError(NOT_A_PARTICIPANT)

        # якщо є активна спроба — завершуємо її стандартним шляхом
        active_attempt = repo.get_active_attempt_for_exam(exam_id, user_id)
        if active_attempt:
            AttemptsService().submit(db, active_attempt.id)

        ok = repo.soft_remove(exam_id, user_id)
        if not ok:
            raise NotFoundError(NOT_A_PARTICIPANT)
        return {"message": "Користувача видалено зі списку учасників іспиту"}

    def set_attendance(self, db: Session, exam_id: UUID, user_id: UUID, update: ExamParticipantAttendanceUpdate):
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND)

        # валідний статус
        target = AttendanceStatusEnum(update.status)

        repo = ExamParticipantsRepository(db)
        ep = repo.set_attendance(exam_id, user_id, target)
        if not ep:
            raise NotFoundError(NOT_A_PARTICIPANT)

        return ExamParticipantResponse.model_validate(ep)
