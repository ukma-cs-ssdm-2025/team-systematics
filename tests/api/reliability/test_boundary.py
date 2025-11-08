from typing import Optional, Self
from fastapi.responses import JSONResponse
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


class MockExamService:
    def create(self, db: pytest.Session, payload: ExamCreate) -> dict:
        if payload.end_at <= payload.start_at:
            raise ValueError("end_at must be after start_at")

        return {
            "id": str(uuid4()),
            "title": payload.title,
            "instructions": payload.instructions,
            "start_at": payload.start_at,
            "end_at": payload.end_at,
            "duration_minutes": payload.duration_minutes,
            "max_attempts": payload.max_attempts,
            "pass_threshold": payload.pass_threshold,
            "owner_id": payload.owner_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

def _create_exam_payload(title: str = "Test Exam", instructions: str = "Test Instructions") -> dict:
    """Helper function to create an exam payload with default values."""
    now = datetime.utcnow()
    return {
        "title": title,
        "instructions": instructions,
        "start_at": (now + timedelta(days=1)).isoformat() + "Z",
        "end_at": (now + timedelta(days=2)).isoformat() + "Z",
        "duration_minutes": 60,
        "max_attempts": 1,
        "pass_threshold": 60,
        "owner_id": str(uuid4())
    }


# Test 1: Exam creation with end_at before start_at
def test_create_exam_end_at_before_start_returns_422():
    """Test that validation rejects exams where end_at is not after start_at."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None

    controller = ExamsController(MockExamService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    now = datetime.utcnow()
    payload = _create_exam_payload()
    payload["start_at"] = now.isoformat() + "Z"
    payload["end_at"] = now.isoformat() + "Z"
    
    response = client.post("/exams", json=payload)
    assert response.status_code == 422
    error_response = response.json()
    assert "detail" in error_response
    assert any("end_at" in error["loc"] for error in error_response["detail"])


# Test 2: Exam creation with the minimum allowed title length
def test_create_exam_with_minimum_title_length_accepted():
    """Boundary test: title with minimal allowed length should pass validation."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None

    class DummyService:
        def create(self, db, payload):
            exam_id = str(uuid4())
            now = datetime.utcnow()
            return {
                "id": exam_id,
                "title": payload.title,
                "instructions": payload.instructions,
                "start_at": payload.start_at,
                "end_at": payload.end_at,
                "duration_minutes": payload.duration_minutes,
                "max_attempts": payload.max_attempts,
                "pass_threshold": payload.pass_threshold,
                "owner_id": payload.owner_id,
                "created_at": now,
                "updated_at": now
            }
            
    controller = ExamsController(DummyService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    payload = _create_exam_payload(title="Abc", instructions="")

    r = client.post("/exams", json=payload)
    # If validation passes, expect the dummy service to be called and return 201
    assert r.status_code in (200, 201)
