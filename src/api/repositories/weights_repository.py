from sqlalchemy.orm import Session
from typing import Dict
from src.models.exams import QuestionType, QuestionTypeWeight

class WeightsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_weights(self) -> Dict[QuestionType, int]:
        """
        Завантажує всі ваги для типів питань з бази даних.

        Returns:
            Словник, де ключ - це QuestionType (enum), а значення - вага (int).
        """
        weights_list = self.db.query(QuestionTypeWeight).all()
        return {w.question_type: w.weight for w in weights_list}