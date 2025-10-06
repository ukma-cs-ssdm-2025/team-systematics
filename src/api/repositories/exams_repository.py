from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from threading import RLock

from ..schemas.exams import Exam, ExamCreate, ExamUpdate

class ExamsRepository:
    def __init__(self) -> None:
        self._items: Dict[UUID, Exam] = {}
        self._lock = RLock()

    def list(self, limit: int, offset: int) -> Tuple[List[Exam], int]:
        with self._lock:
            items = list(self._items.values())
            total = len(items)
            return items[offset: offset + limit], total

    def get(self, exam_id: UUID) -> Optional[Exam]:
        return self._items.get(exam_id)

    def create(self, payload: ExamCreate) -> Exam:
        with self._lock:
            new_id = uuid4()
            item = Exam(
                id=new_id,
                title=payload.title,
                instructions=payload.instructions,
                start_at=payload.start_at,
                end_at=payload.end_at,
                duration_minutes=payload.duration_minutes,
                max_attempts=payload.max_attempts,
                pass_threshold=payload.pass_threshold,
                owner_id=payload.owner_id,
                question_count=0,
            )
            self._items[new_id] = item
            return item

    def update(self, exam_id: UUID, patch: dict | ExamUpdate) -> Optional[Exam]:
        with self._lock:
            cur = self._items.get(exam_id)
            if not cur:
                return None
            data = cur.model_dump()
            patch_data = patch.model_dump(exclude_unset=True) if hasattr(patch, 'model_dump') else {k: v for k, v in patch.items() if v is not None}
            data.update(patch_data)
            updated = Exam(**data)
            self._items[exam_id] = updated
            return updated

    def delete(self, exam_id: UUID) -> bool:
        with self._lock:
            return self._items.pop(exam_id, None) is not None