from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas import exam as exam_schemas
from typing import List

router = APIRouter()

@router.get("/exams", response_model=List[exam_schemas.ExamSchema])
def list_exams(db: Session = Depends(get_db)):
    # Тут буде логіка для отримання всіх іспитів
    # Наприклад: return db.query(Exam).all()
    pass

@router.post("/exams", response_model=exam_schemas.ExamSchema)
def create_exam(exam_in: exam_schemas.ExamCreate, db: Session = Depends(get_db)):
    # Логіка створення іспиту
    pass

@router.post("/exams/{exam_id}/attempts", response_model=exam_schemas.AttemptSchema)
def start_exam_attempt(exam_id: str, db: Session = Depends(get_db)):
    # Логіка для початку нової спроби
    pass

@router.get("/exams", response_model=exam_schemas.ExamsResponse)
def get_all_exams(db: Session = Depends(get_db)):
    """
    Отримує список майбутніх та завершених іспитів.
    Логіка винесена у exam_service.
    """
    return exam_service.get_exams(db)