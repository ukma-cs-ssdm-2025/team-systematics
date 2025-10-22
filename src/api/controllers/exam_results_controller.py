from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


from src.api.database import get_db
from src.api.schemas.attempts import AttemptResultResponse
from src.api.services.exam_results_service import get_attempt_result


router = APIRouter(prefix="/api/v1/exams", tags=["exam-results"])




@router.get("/{exam_id}/attempts/{attempt_id}/result", response_model=AttemptResultResponse)
def read_attempt_result(
    exam_id: UUID,
    attempt_id: UUID,
    db: Session = Depends(get_db),
):
# TODO(auth): restrict access to owner / teacher / supervisor
    try:
        result = get_attempt_result(db, exam_id=exam_id, attempt_id=attempt_id)
        return result
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")