from sqlalchemy.orm import Session
from fastapi import APIRouter, Query, Path, status, Depends
from uuid import UUID
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from src.api.schemas.attempts import AttemptStartRequest, Attempt
from src.api.services.exams_service import ExamsService
from .versioning import require_api_version
from src.api.database import get_db

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])

        @self.router.get("", response_model=ExamsPage, summary="List exams")
        async def list_exams(db: Session = Depends(get_db), limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
            return self.service.list(db, limit=limit, offset=offset)

        @self.router.post("", response_model=Exam, status_code=status.HTTP_201_CREATED, summary="Create exam")
        async def create_exam(payload: ExamCreate, db: Session = Depends(get_db)):
            return self.service.create(db, payload)

        @self.router.get("/{exam_id}", response_model=Exam, summary="Get exam by id")
        async def get_exam(exam_id: UUID, db: Session = Depends(get_db)):
            return self.service.get(db, exam_id)

        @self.router.patch("/{exam_id}", response_model=Exam, summary="Update exam (partial)")
        async def update_exam(patch: ExamUpdate, exam_id: UUID, db: Session = Depends(get_db)):
            return self.service.update(db, exam_id, patch)

        @self.router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete exam")
        async def delete_exam(exam_id: UUID, db: Session = Depends(get_db)):
            self.service.delete(db, exam_id)
            return None

        @self.router.post("/{exam_id}/attempts", response_model=Attempt, status_code=status.HTTP_201_CREATED, summary="Start an attempt for exam")
        async def start_attempt(payload: AttemptStartRequest, exam_id: UUID, db: Session = Depends(get_db)):
            return self.service.start_attempt(db, exam_id, payload)