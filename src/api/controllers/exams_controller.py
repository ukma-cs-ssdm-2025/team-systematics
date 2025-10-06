from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Query, Path, status, Depends

from ..schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage
from ..schemas.attempts import AttemptStartRequest, Attempt
from ..services.exams_service import ExamsService
from .versioning import require_api_version

class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/exams", tags=["Exams"], dependencies=[Depends(require_api_version)])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "", self.list_exams, methods=["GET"],
            response_model=ExamsPage,
            summary="List exams",
        )
        self.router.add_api_route(
            "", self.create_exam, methods=["POST"],
            response_model=Exam, status_code=status.HTTP_201_CREATED,
            summary="Create exam",
        )
        self.router.add_api_route(
            "/{exam_id}", self.get_exam, methods=["GET"],
            response_model=Exam,
            summary="Get exam by id",
        )
        self.router.add_api_route(
            "/{exam_id}", self.update_exam, methods=["PATCH"],
            response_model=Exam,
            summary="Update exam (partial)",
        )
        self.router.add_api_route(
            "/{exam_id}", self.delete_exam, methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete exam",
        )
        self.router.add_api_route(
            "/{exam_id}/attempts", self.start_attempt, methods=["POST"],
            response_model=Attempt, status_code=status.HTTP_201_CREATED,
            summary="Start an attempt for exam",
        )

    # Handlers
    async def list_exams(self, limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)) -> ExamsPage:
        return self.service.list(limit=limit, offset=offset)

    async def create_exam(self, payload: ExamCreate) -> Exam:
        return self.service.create(payload)

    async def get_exam(self, exam_id: UUID = Path(..., description="Exam id")) -> Exam:
        return self.service.get(exam_id)

    async def update_exam(self, exam_id: UUID, patch: ExamUpdate) -> Exam:
        return self.service.update(exam_id, patch)

    async def delete_exam(self, exam_id: UUID):
        self.service.delete(exam_id)
        return None

    async def start_attempt(self, exam_id: UUID, payload: AttemptStartRequest) -> Attempt:
        return self.service.start_attempt(exam_id, payload)