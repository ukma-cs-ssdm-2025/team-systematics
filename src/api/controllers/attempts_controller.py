from uuid import UUID
from fastapi import APIRouter, status, Depends

from ..schemas.attempts import AnswerUpsert, Answer, Attempt
from ..services.attempts_service import AttemptsService
from .versioning import require_api_version

class AttemptsController:
    def __init__(self, service: AttemptsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/attempts", tags=["Attempts"], dependencies=[Depends(require_api_version)])

        @self.router.post("/{attempt_id}/answers", response_model=Answer, status_code=status.HTTP_201_CREATED,
                          summary="Save or update an answer within an attempt")
        async def add_answer(attempt_id: UUID, payload: AnswerUpsert) -> Answer:
            return self.service.add_answer(attempt_id, payload)

        @self.router.post("/{attempt_id}/submit", response_model=Attempt,
                          summary="Submit attempt")
        async def submit(attempt_id: UUID) -> Attempt:
            return self.service.submit(attempt_id)