from sqlalchemy.orm import Session
from uuid import UUID
# НОВЕ: Імпортуємо Optional для сумісності з Python 3.9
from typing import List, Tuple, Optional
from src.models.exams import Exam
from src.api.schemas.exams import ExamCreate, ExamUpdate

class ExamsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, limit: int, offset: int) -> Tuple[List[Exam], int]:
        total = self.db.query(Exam).count()
        items = self.db.query(Exam).offset(offset).limit(limit).all()
        return items, total

    # ВИПРАВЛЕНО: Замінено 'Exam | None' на 'Optional[Exam]'
    def get(self, exam_id: UUID) -> Optional[Exam]:
        return self.db.query(Exam).filter(Exam.id == exam_id).first()

    def create(self, payload: ExamCreate) -> Exam:
        new_exam = Exam(**payload.model_dump())
        self.db.add(new_exam)
        self.db.commit()
        self.db.refresh(new_exam)
        return new_exam

    # ВИПРАВЛЕНО: Замінено 'Exam | None' на 'Optional[Exam]'
    def update(self, exam_id: UUID, patch: ExamUpdate) -> Optional[Exam]:
        exam = self.get(exam_id)
        if not exam:
            return None
        
        patch_data = patch.model_dump(exclude_unset=True)
        for key, value in patch_data.items():
            setattr(exam, key, value)
            
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def delete(self, exam_id: UUID) -> bool:
        exam = self.get(exam_id)
        if not exam:
            return False
        
        self.db.delete(exam)
        self.db.commit()
        return True