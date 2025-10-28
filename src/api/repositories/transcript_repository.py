from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from src.models.exams import Exam
from src.models.attempts import Attempt

class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_exams(self) -> List[Exam]:
        """
        Повертає список усіх іспитів.
        """
        return self.db.query(Exam).all()

    def get_all_attempts_by_user(self, user_id: UUID) -> List[Attempt]:
        """
        Завантажує всі спроби для конкретного користувача.
        """
        return self.db.query(Attempt).filter(Attempt.user_id == user_id).all()