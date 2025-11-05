from sqlalchemy.orm import Session
from fastapi import APIRouter, Query, Path, status, Depends
from uuid import UUID
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from src.api.schemas.attempts import Attempt
from src.models.users import User
from src.utils.auth import get_current_user_id, get_current_user 
from src.api.services.exams_service import ExamsService
from .versioning import require_api_version
from src.api.database import get_db

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])

        @self.router.get("", summary="List exams")
        async def list_exams(
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user),
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0)
            ):
            return self.service.list(db, user_id=current_user.id, limit=limit, offset=offset)

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
        async def start_attempt(user_id: UUID = Depends(get_current_user_id), exam_id: UUID = Path(...), db: Session = Depends(get_db)):
            return self.service.start_attempt(db, exam_id, user_id)

        # --- Question endpoints (teachers can manage questions before publishing) ---
        @self.router.post("/{exam_id}/questions", status_code=status.HTTP_201_CREATED, summary="Create question for exam")
        async def create_question(exam_id: UUID, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            # Optional: check that current_user is owner/teacher - left to service/repo to enforce
            return self.service.create_question(db, exam_id, payload)

        @self.router.patch("/{exam_id}/questions/{question_id}", summary="Update question")
        async def update_question(exam_id: UUID, question_id: UUID, patch: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.update_question(db, question_id, patch)

        @self.router.delete("/{exam_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete question")
        async def delete_question(exam_id: UUID, question_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            self.service.delete_question(db, question_id)
            return None

        # Option endpoints
        @self.router.post("/{exam_id}/questions/{question_id}/options", status_code=status.HTTP_201_CREATED, summary="Create option for question")
        async def create_option(exam_id: UUID, question_id: UUID, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.create_option(db, question_id, payload)

        @self.router.patch("/{exam_id}/questions/{question_id}/options/{option_id}", summary="Update option")
        async def update_option(exam_id: UUID, question_id: UUID, option_id: UUID, patch: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            return self.service.update_option(db, option_id, patch)

        @self.router.delete("/{exam_id}/questions/{question_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete option")
        async def delete_option(exam_id: UUID, question_id: UUID, option_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
            self.service.delete_option(db, option_id)
            return None