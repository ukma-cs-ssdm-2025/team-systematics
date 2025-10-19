from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
# НОВЕ: Імпортуємо Optional
from typing import Optional
from src.models.exam import Attempt, Answer
from src.api.schemas.attempts import AnswerUpsert

class AttemptsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_attempt(self, exam_id: UUID, user_id: UUID, duration_minutes: int) -> Attempt:
        due_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        new_attempt = Attempt(
            exam_id=exam_id,
            user_id=user_id,
            status="in_progress",
            started_at=datetime.utcnow(),
            due_at=due_at
        )
        self.db.add(new_attempt)
        self.db.commit()
        self.db.refresh(new_attempt)
        return new_attempt

    # ВИПРАВЛЕНО: Замінено 'Attempt | None' на 'Optional[Attempt]'
    def get_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        return self.db.query(Attempt).filter(Attempt.id == attempt_id).first()

    def upsert_answer(self, attempt_id: UUID, payload: AnswerUpsert) -> Answer:
        answer_value = {
            "text": payload.text,
            "selected_option_ids": [str(uuid) for uuid in payload.selected_option_ids] if payload.selected_option_ids else None
        }

        answer = self.db.query(Answer).filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == payload.question_id
        ).first()

        if answer:
            answer.value = answer_value
        else:
            answer = Answer(
                attempt_id=attempt_id,
                question_id=payload.question_id,
                value=answer_value
            )
            self.db.add(answer)
        
        self.db.commit()
        self.db.refresh(answer)
        return answer

    # ВИПРАВЛЕНО: Замінено 'Attempt | None' на 'Optional[Attempt]'
    def submit_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        attempt = self.get_attempt(attempt_id)
        if not attempt:
            return None
        
        attempt.status = "submitted"
        attempt.submitted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attempt)
        return attempt