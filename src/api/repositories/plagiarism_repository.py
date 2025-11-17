from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.attempts import PlagiarismCheck, PlagiarismStatus


class PlagiarismRepository:
    @staticmethod
    def get_by_attempt_id(db: Session, attempt_id: UUID) -> Optional[PlagiarismCheck]:
        return (
            db.query(PlagiarismCheck)
            .filter(PlagiarismCheck.attempt_id == attempt_id)
            .one_or_none()
        )

    def create_or_update(
        self,
        db: Session,
        *,
        attempt_id: UUID,
        uniqueness_percent: float,
        max_similarity: float,
        status: PlagiarismStatus,
        details: Optional[Dict[str, Any]] = None,
    ) -> PlagiarismCheck:
        existing = self.get_by_attempt_id(db, attempt_id)
        if existing:
            existing.uniqueness_percent = uniqueness_percent
            existing.max_similarity = max_similarity
            existing.status = status
            existing.details = details
            return existing

        check = PlagiarismCheck(
            attempt_id=attempt_id,
            uniqueness_percent=uniqueness_percent,
            max_similarity=max_similarity,
            status=status,
            details=details,
        )
        db.add(check)
        return check

    @staticmethod
    def list_by_exam_with_filter(
        db: Session,
        *,
        exam_id: UUID,
        max_uniqueness: Optional[float] = None,
    ) -> List[PlagiarismCheck]:
        """
        Опціонально: щоб потім можна було робити фільтр типу "<70% унікальності".
        """
        q = (
            db.query(PlagiarismCheck)
            .join(PlagiarismCheck.attempt)  # relationship з Attempt
            .filter(PlagiarismCheck.attempt.has(exam_id=exam_id))
        )
        if max_uniqueness is not None:
            q = q.filter(PlagiarismCheck.uniqueness_percent <= max_uniqueness)
        return q.all()
