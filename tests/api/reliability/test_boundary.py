from typing import Optional, Self
import pytest
from fastapi import APIRouter, Depends, FastAPI, status
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta

from src.api.schemas.exams import Exam, ExamCreate
from src.api.services.exams_service import ExamsService
from src.api.controllers.exams_controller import ExamsController
from src.api.controllers.versioning import require_api_version
from src.api.database import get_db


class ExamsController:
    def __init__(self, service: ExamsService) -> None:
        self.service = service
        self.router = APIRouter(prefix="/exams", tags=["Exams"])

        self.router.add_api_route(
            "", self.create_exam, methods=["POST"], response_model=Exam, status_code=status.HTTP_201_CREATED, summary="Create exam"
        )

    async def create_exam(self, payload: ExamCreate, db: Optional[pytest.Session] = Depends(get_db)):
        exam = self.service.create(db, payload)
        
        return {
            "id": str(uuid4()),
            "title": payload.title,
            "instructions": payload.instructions,
            "start_at": payload.start_at,
            "end_at": payload.end_at,
            "duration_minutes": payload.duration_minutes,
            "max_attempts": payload.max_attempts,
            "pass_threshold": payload.pass_threshold,
            "owner_id": payload.owner_id
        }


def _payload_with_dates(start_at, end_at):
    return {
        "title": "Boundary Exam",
        "instructions": "Boundary test",
        "start_at": start_at,
        "end_at": end_at,
        "duration_minutes": 60,
        "max_attempts": 1,
        "pass_threshold": 60,
        "owner_id": str(uuid4()),
    }


# Test 1: Exam creation with end_at before start_at
def test_create_exam_end_at_before_start_returns_422():
    """Validation should reject exams where end_at is not after start_at."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None

    class DummyService:
        def create(self, db, payload):
            # Просто повертає id як приклад
            return {"id": str(uuid4())}

    controller = ExamsController(DummyService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    now = datetime.utcnow().isoformat() + "Z"
    # end_at equal to start_at (boundary) -> invalid
    payload = _payload_with_dates(now, now)
    r = client.post("/exams", json=payload)
    assert r.status_code == 422


# Test 2: Exam creation with the minimum allowed title length
def test_create_exam_with_minimum_title_length_accepted():
    """Boundary test: title with minimal allowed length should pass validation."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None

    class DummyService:
        def create(self, db, payload):
            # Просто повертає id як приклад
            return {"id": str(uuid4())}

    controller = ExamsController(DummyService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    now = datetime.utcnow()
    payload = {
        "title": "Abc",  # minimal (3 chars)
        "instructions": "",
        "start_at": (now + timedelta(days=1)).isoformat() + "Z",
        "end_at": (now + timedelta(days=1, hours=1)).isoformat() + "Z",
        "duration_minutes": 60,
        "max_attempts": 1,
        "pass_threshold": 60,
        "owner_id": str(uuid4()),
    }

    r = client.post("/exams", json=payload)
    # If validation passes, expect the dummy service to be called and return 201
    assert r.status_code in (200, 201)
