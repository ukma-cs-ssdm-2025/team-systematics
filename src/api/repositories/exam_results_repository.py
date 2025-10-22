# api/repositories/exam_results_repository.py
from __future__ import annotations

from typing import Any, Dict
from uuid import UUID
from sqlalchemy.orm import Session

# Імпортуємо готовий SQL
from src.api.repositories.sql_queries import _SQL

def get_attempt_result_raw(db: Session, attempt_id: UUID) -> Dict[str, Any]:
    """
    Fetch one row of aggregates for the attempt. Returns a dict containing:
    - exam_title
    - attempt_status
    - time_spent_seconds
    - total_questions
    - max_points
    - answers_given
    - correct_answers
    - incorrect_answers
    - pending_count
    - earned_points
    """
    row = db.execute(_SQL, {"attempt_id": attempt_id}).mappings().first()
    if not row:
        return {}

    # Ensure non-negative time spent seconds
    spent = int(row.get("raw_spent_seconds") or 0)
    if spent < 0:
        spent = 0

    return {
        "exam_title": row["exam_title"],
        "attempt_status": row["attempt_status"],
        "time_spent_seconds": spent,
        "total_questions": int(row["total_questions"] or 0),
        "max_points": float(row["max_points"] or 0.0),
        "answers_given": int(row["answers_given"] or 0),
        "correct_answers": int(row["correct_answers"] or 0),
        "incorrect_answers": int(row["incorrect_answers"] or 0),
        "pending_count": int(row["pending_count"] or 0),
        "earned_points": float(row["earned_points"] or 0.0),
    }
