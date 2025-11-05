from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from uuid import uuid4

from src.models.users import User

from src.api.controllers.transcript_controller import TranscriptController

from src.api.services.transcript_service import TranscriptService
from src.api.schemas.transcript import TranscriptResponse, Statistics, CourseResult
from src.api.database import get_db
from src.utils.auth import get_current_user_with_role


@pytest.fixture
def mock_transcript_service():
    return MagicMock(spec=TranscriptService)

@pytest.fixture
def student_user():
    user = User(id=uuid4(), email="student@example.com")
    user.role = "student"
    return user


@pytest.fixture
def teacher_user():
    user = User(id=uuid4(), email="teacher@example.com")
    user.role = "teacher"
    return user

@pytest.fixture
def client(mock_transcript_service, student_user):
    app = FastAPI()
    controller = TranscriptController(mock_transcript_service)
    app.include_router(controller.router)

    app.dependency_overrides[get_current_user_with_role] = lambda: student_user
    
    def fake_db():
        yield MagicMock()
        
    app.dependency_overrides[get_db] = fake_db

    return TestClient(app)


def test_get_transcript_success(client, mock_transcript_service, student_user):
    mock_response = TranscriptResponse(
        courses=[CourseResult(id=uuid4(), course_name="Test Course", rating=95, ects_grade="A", national_grade="Відмінно", pass_status="Так")],
        statistics=Statistics(completed_courses=1, total_courses=1, a_grades_count=1, average_rating=95)
    )
    mock_transcript_service.get_transcript_for_user.return_value = mock_response

    response = client.get("/transcript")
    
    assert response.status_code == 200
    assert response.json() == mock_response.model_dump(mode='json')
    
    mock_transcript_service.get_transcript_for_user.assert_called_once()
    call_args, _ = mock_transcript_service.get_transcript_for_user.call_args
    assert call_args[0] == student_user.id
    assert isinstance(call_args[1], MagicMock)

def test_access_control_teacher_forbidden(client, mock_transcript_service, teacher_user):
    client.app.dependency_overrides[get_current_user_with_role] = lambda: teacher_user
    
    response = client.get("/transcript")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Доступно лише для студентів"
    
    mock_transcript_service.get_transcript_for_user.assert_not_called()
    
    del client.app.dependency_overrides[get_current_user_with_role]