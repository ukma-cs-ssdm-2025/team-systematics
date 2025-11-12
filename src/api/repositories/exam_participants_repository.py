from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.exam_participants import ExamParticipant, AttendanceStatusEnum
from src.models.attempts import Attempt, AttemptStatus
from src.models.courses import CourseEnrollment

class ExamParticipantsRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- CRUD / списки ---
    def list_active(self, exam_id: UUID) -> List[ExamParticipant]:
        return (
            self.db.query(ExamParticipant)
            .filter(and_(ExamParticipant.exam_id == exam_id, ExamParticipant.is_active == True))
            .all()
        )

    def get(self, exam_id: UUID, user_id: UUID) -> Optional[ExamParticipant]:
        return (
            self.db.query(ExamParticipant)
            .filter(and_(ExamParticipant.exam_id == exam_id, ExamParticipant.user_id == user_id))
            .first()
        )

    def add(self, exam_id: UUID, user_id: UUID) -> ExamParticipant:
        ep = self.get(exam_id, user_id)
        if ep:
            ep.is_active = True
            ep.removed_at = None
        else:
            ep = ExamParticipant(exam_id=exam_id, user_id=user_id)
            self.db.add(ep)
        self.db.commit()
        self.db.refresh(ep)
        return ep

    def soft_remove(self, exam_id: UUID, user_id: UUID) -> bool:
        ep = self.get(exam_id, user_id)
        if not ep or ep.is_active is False:
            return False
        ep.is_active = False
        ep.removed_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    # Відвідуваність
    def set_attendance(self, exam_id: UUID, user_id: UUID, status: AttendanceStatusEnum) -> Optional[ExamParticipant]:
        ep = self.get(exam_id, user_id)
        if not ep:
            return None
        ep.attendance_status = status
        self.db.commit()
        self.db.refresh(ep)
        return ep

    # Перевірки
    def is_user_enrolled_to_course(self, course_id: UUID, user_id: UUID) -> bool:
        exists = (
            self.db.query(CourseEnrollment)
            .filter(and_(CourseEnrollment.course_id == course_id, CourseEnrollment.user_id == user_id))
            .first()
        )
        return bool(exists)

    def has_active_attempt_in_other_exam(self, user_id: UUID, exam_id_to_join: UUID) -> bool:
        """
        Чи є в юзера активна спроба (in_progress) в ІНШОМУ іспиті.
        """
        return (
            self.db.query(Attempt)
            .filter(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.status == AttemptStatus.in_progress,
                    Attempt.exam_id != exam_id_to_join,
                )
            )
            .first()
            is not None
        )

    def get_active_attempt_for_exam(self, exam_id: UUID, user_id: UUID) -> Optional[Attempt]:
        return (
            self.db.query(Attempt)
            .filter(
                and_(
                    Attempt.exam_id == exam_id,
                    Attempt.user_id == user_id,
                    Attempt.status == AttemptStatus.in_progress,
                )
            )
            .first()
        )
