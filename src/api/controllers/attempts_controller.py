from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import APIRouter, status, Depends
from src.api.schemas.attempts import AnswerUpsert, Answer, Attempt, AttemptResultResponse
from src.api.schemas.exam_review import ExamAttemptReviewResponse
from src.api.services.attempts_service import AttemptsService
from src.api.services.exam_review_service import ExamReviewService
from .versioning import require_api_version
from src.api.database import get_db
from src.models.users import User
from src.api.dependencies import get_current_user

class AttemptsController:
    def __init__(self, service: AttemptsService, review_service: ExamReviewService) -> None:
        self.service = service
        self.review_service = review_service
        self.router = APIRouter(prefix="/attempts", tags=["Attempts"], dependencies=[Depends(require_api_version)])

        @self.router.post("/{attempt_id}/answers", response_model=Answer, status_code=status.HTTP_201_CREATED, summary="Save or update an answer")
        async def add_answer(payload: AnswerUpsert, attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.add_answer(db, attempt_id, payload)

        @self.router.post("/{attempt_id}/submit", response_model=Attempt, summary="Submit attempt")
        async def submit(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.submit(db, attempt_id)

        @self.router.get("/{attempt_id}", summary="Get attempt details for UI")
        async def get_attempt_details(attempt_id: UUID, db: Session = Depends(get_db)):
            return self.service.get_attempt_details(db, attempt_id)

        @self.router.get("/{attempt_id}/results", response_model=AttemptResultResponse, summary="Send exam results")
        async def read_attempt_result(
            attempt_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            return self.service.get_attempt_result(
                db,
                attempt_id=attempt_id,
                current_user=current_user,
            )


        @self.router.get("/{attempt_id}/review", response_model=ExamAttemptReviewResponse,
            summary="Отримати детальний огляд спроби іспиту")
        async def get_exam_attempt_review(
            attempt_id: UUID,
            db: Session = Depends(get_db),
        ):
            return self.review_service.get_attempt_review(attempt_id=attempt_id, db=db)