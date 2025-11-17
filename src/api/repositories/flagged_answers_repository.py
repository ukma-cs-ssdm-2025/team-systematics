from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.attempts import FlaggedAnswer, Answer
from src.models.attempts import Attempt
from src.models.exams import Exam
from src.models.users import User


class FlaggedAnswersRepository:
    @staticmethod
    def get_by_answer_id(db: Session, answer_id: UUID) -> Optional[FlaggedAnswer]:
        """Отримати позначену відповідь за ID відповіді"""
        return (
            db.query(FlaggedAnswer)
            .filter(FlaggedAnswer.answer_id == answer_id)
            .one_or_none()
        )

    @staticmethod
    def create(db: Session, answer_id: UUID) -> FlaggedAnswer:
        """Створити позначення для відповіді"""
        flagged = FlaggedAnswer(answer_id=answer_id)
        db.add(flagged)
        db.flush()
        return flagged

    def delete(self, db: Session, answer_id: UUID) -> bool:
        """Видалити позначення для відповіді"""
        flagged = self.get_by_answer_id(db, answer_id)
        if flagged:
            db.delete(flagged)
            return True
        return False

    @staticmethod
    def list_all(db: Session) -> List[FlaggedAnswer]:
        """Отримати всі позначені відповіді з повною інформацією"""
        return (
            db.query(FlaggedAnswer)
            .join(Answer, Answer.id == FlaggedAnswer.answer_id)
            .join(Attempt, Attempt.id == Answer.attempt_id)
            .join(Exam, Exam.id == Attempt.exam_id)
            .join(User, User.id == Attempt.user_id)
            .order_by(FlaggedAnswer.flagged_at.desc())
            .all()
        )

    def is_flagged(self, db: Session, answer_id: UUID) -> bool:
        """Перевірити, чи позначена відповідь"""
        return self.get_by_answer_id(db, answer_id) is not None

