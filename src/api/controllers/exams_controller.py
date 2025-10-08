from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Query, Path, status, Depends

from ..schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from ..schemas.attempts import AttemptStartRequest, Attempt
from ..services.exams_service import ExamsService
from .versioning import require_api_version

EXAMPLE_EXAM_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])

        @self.router.get("", response_model=ExamsPage, summary="List exams")
        async def list_exams(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)) -> ExamsPage:
            return self.service.list(limit=limit, offset=offset)

        @self.router.post("", response_model=Exam, status_code=status.HTTP_201_CREATED, summary="Create exam")
        async def create_exam(payload: ExamCreate) -> Exam:
            return self.service.create(payload)

        @self.router.get("/{exam_id}", response_model=Exam, summary="Get exam by id")
        async def get_exam(
            exam_id: UUID = Path(
                ...,
                description="Exam id",
                example=EXAMPLE_EXAM_ID
            )
        ) -> Exam:
            return self.service.get(exam_id)

        @self.router.patch("/{exam_id}", response_model=Exam, summary="Update exam (partial)")
        async def update_exam(
            patch: ExamUpdate,
            exam_id: UUID = Path(
                ...,
                description="Exam id",
                example=EXAMPLE_EXAM_ID
            )
        ) -> Exam:
            return self.service.update(exam_id, patch)

        @self.router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete exam")
        async def delete_exam(
            exam_id: UUID = Path(
                ...,
                description="Exam id",
                example=EXAMPLE_EXAM_ID
            )
        ):
            self.service.delete(exam_id)
            return None

        @self.router.post("/{exam_id}/attempts", response_model=Attempt, status_code=status.HTTP_201_CREATED, summary="Start an attempt for exam")
        async def start_attempt(
            payload: AttemptStartRequest,
            exam_id: UUID = Path(
                ...,
                description="Exam id",
                example=EXAMPLE_EXAM_ID
            )
        ) -> Attempt:
            return self.service.start_attempt(exam_id, payload)