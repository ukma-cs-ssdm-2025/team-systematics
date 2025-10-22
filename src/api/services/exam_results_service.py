from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session


from src.api.repositories.exam_results_repository import get_attempt_result_raw
from src.api.schemas.attempts import AttemptResultResponse




def get_attempt_result(db: Session, exam_id: UUID, attempt_id: UUID) -> AttemptResultResponse:
    data = get_attempt_result_raw(db, attempt_id)
    if not data:
# Let the controller decide how to map this to HTTP; keep service pure.
        raise LookupError("attempt_not_found")


# Compute score percent with DB weights (no rounding) and guard against /0
    max_points = float(data["max_points"]) if data["max_points"] else 0.0
    earned = float(data["earned_points"]) if data["earned_points"] else 0.0
    score_percent = (100.0 * earned / max_points) if max_points > 0 else 0.0


# Determine final status: completed iff no pending
    status = str(data["attempt_status"] or "in_progress")
    if data["pending_count"] == 0 and status in ("submitted", "completed"):
        status = "completed"


# Build response DTO
    return AttemptResultResponse(
        exam_title=data["exam_title"],
        status=status,
        score_percent=score_percent,
        time_spent_seconds=int(data["time_spent_seconds"] or 0),
        total_questions=int(data["total_questions"] or 0),
        answers_given=int(data["answers_given"] or 0),
        correct_answers=int(data["correct_answers"] or 0),
        incorrect_answers=int(data["incorrect_answers"] or 0),
    )