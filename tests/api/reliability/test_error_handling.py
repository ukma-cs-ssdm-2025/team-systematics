from typing import Optional
import pytest
from fastapi import FastAPI, status, APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.api.schemas.exams import Exam, ExamCreate
from src.api.services.exams_service import ExamsService
from src.api.database import get_db
from src.api.controllers.versioning import require_api_version
from src.api.controllers.exams_controller import ExamsController
from src.utils.auth import get_current_user


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    
    def __init__(self, message: str = "A database connection error occurred"):
        super().__init__(message)
        self.message = message


class ExplodingService:
    """Mock service that simulates database errors"""
    def create(self, db: Session, payload: ExamCreate, owner_id=None) -> Exam:
        raise DatabaseConnectionError("Database connection failed")


class ValidationService:
    """Mock service that simulates validation errors"""
    def create(self, db: Session, payload: ExamCreate, owner_id=None) -> Exam:
        if not payload.title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VALIDATION_ERROR", "message": "Title cannot be empty"}
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Invalid exam data"}
        )


class DummyService:
    """Mock service that returns valid exam objects"""
    def create(self, db: Session, payload: ExamCreate, owner_id=None) -> Exam:
        # Використовуємо now(timezone.utc) замість utcnow() для отримання часу в UTC
        now = datetime.now(timezone.utc)
        exam_dict = {
            "id": str(uuid4()),
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
        return Exam(**exam_dict)


def _valid_exam_payload():
    now = datetime.now(timezone.utc)
    return {
        "title": "Test Exam",
        "instructions": "Do your best",
        "start_at": (now + timedelta(days=1)).isoformat(),
        "end_at": (now + timedelta(days=2)).isoformat(),
        "duration_minutes": 60,
        "max_attempts": 1,
        "pass_threshold": 60,
        "owner_id": str(uuid4())
    }


# Test: Database error handling
def test_create_exam_database_error_returns_500():
    """Test that database errors are properly handled and return 500 status code."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None
    
    controller = ExamsController(ExplodingService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    dummy_user = type("User", (), {"id": uuid4()})
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    dummy_user = type("User", (), {"id": uuid4()})
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    client = TestClient(app)
    
    payload = _valid_exam_payload()
    response = client.post("/exams", json=payload)
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    error_response = response.json()
    assert "detail" in error_response
    assert error_response["detail"]["code"] == "INTERNAL_ERROR"
    assert "Database connection failed" in error_response["detail"]["message"]


# Test: Validation error handling
def test_create_exam_validation_error_returns_422():
    """Test that validation errors are properly handled and return 422 status code."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None
    
    controller = ExamsController(ValidationService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    dummy_user = type("User", (), {"id": uuid4()})
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    client = TestClient(app)
    
    payload = _valid_exam_payload()
    response = client.post("/exams", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_response = response.json()
    assert "detail" in error_response
    assert error_response["detail"]["code"] == "VALIDATION_ERROR"
    assert "Invalid exam data" in error_response["detail"]["message"]


# Test: Empty title validation
def test_create_exam_empty_title_validation():
    """Test that empty title fails FastAPI validation with 422 status code."""
    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None
    
    controller = ExamsController(ValidationService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    dummy_user = type("User", (), {"id": uuid4()})
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    client = TestClient(app)
    
    payload = _valid_exam_payload()
    payload["title"] = ""  # Set empty title
    response = client.post("/exams", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_response = response.json()
    assert "detail" in error_response
    assert isinstance(error_response["detail"], list)
    assert any("title" in e["loc"] for e in error_response["detail"])
