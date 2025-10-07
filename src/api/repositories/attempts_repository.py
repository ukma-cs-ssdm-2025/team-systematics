from __future__ import annotations
from typing import Dict, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from threading import RLock

from ..schemas.attempts import Attempt, Answer

class AttemptsRepository:
    def __init__(self) -> None:
        self._attempts: Dict[UUID, Attempt] = {}
        # answers[attempt_id][question_id] -> Answer
        self._answers: Dict[UUID, Dict[UUID, Answer]] = {}
        self._lock = RLock()

    def create_attempt(self, exam_id: UUID, user_id: UUID, duration_minutes: int) -> Attempt:
        with self._lock:
            attempt_id = uuid4()
            now = datetime.utcnow()
            due = now + timedelta(minutes=duration_minutes, seconds=300)
            att = Attempt(
                id=attempt_id,
                exam_id=exam_id,
                user_id=user_id,
                status="in_progress",
                started_at=now,
                due_at=due,
                submitted_at=None,
                score_percent=None,
            )
            self._attempts[attempt_id] = att
            self._answers[attempt_id] = {}
            return att

    def get_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        return self._attempts.get(attempt_id)

    def upsert_answer(self, attempt_id: UUID, question_id: UUID, text: str | None, selected_option_ids: list[UUID] | None) -> Answer:
        with self._lock:
            if attempt_id not in self._answers:
                self._answers[attempt_id] = {}
            ans_id = uuid4()
            ans = Answer(
                id=ans_id,
                attempt_id=attempt_id,
                question_id=question_id,
                text=text,
                selected_option_ids=selected_option_ids,
                saved_at=datetime.utcnow(),
            )
            self._answers[attempt_id][question_id] = ans
            return ans

    def submit_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        with self._lock:
            att = self._attempts.get(attempt_id)
            if not att:
                return None
            if att.status != "in_progress":
                return att
            att = att.model_copy(update={"status": "submitted", "submitted_at": datetime.utcnow()})
            self._attempts[attempt_id] = att
            return att