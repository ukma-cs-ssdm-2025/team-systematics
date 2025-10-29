from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from uuid import uuid4

from src.models.users import User
from src.api.controllers.transcript_controller import TranscriptController
from src.api.services.transcript_service import TranscriptService
from src.api.schemas.transcript import Statistics, TranscriptResponse
from src.api.database import get_db
from src.utils.auth import get_current_user, get_user_role


@pytest.fixture
def mock_transcript_service():
    mock_service = MagicMock()

    mock_service.get_transcript_for_user.return_value = TranscriptResponse(
        courses=[{
            "id": uuid4(),
            "course_name": "Test Course 1",
            "grade": "A",
            "course_id": uuid4()
        }],
        overall_grade=90,
        total_courses=5,
        statistics=Statistics(
            completed_courses=4,
            total_courses=5,
            a_grades_count=3,
            average_rating=4.5
        )
    )

    return mock_service

@pytest.fixture
def client(mock_transcript_service):
    app = FastAPI()

    controller = TranscriptController(mock_transcript_service)
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password_here",
        created_at="2025-10-28T00:00:00",
        first_name="Test",
        last_name="User",
        patronymic="Patronymic",
        major=None,
        role="student"
    )

    app.dependency_overrides[get_user_role] = lambda db, user_id: "student"

    app.dependency_overrides[get_db] = _fake_db

    return TestClient(app)



def test_sort_tests_by_column(client):
    # Симулюємо запит для сортування за назвою тесту
    response = client.get("/transcript", params={"sort_by": "course_name"})
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert data["courses"][0]["course_name"] == "Test Course 1"

    response = client.get("/transcript", params={"sort_by": "rating"})
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert data["courses"][0]["rating"] is None



def test_sort_average_grade(client):
    response = client.get("/transcript", params={"sort_by": "course_name"})
    
    assert response.status_code == 200  # Очікуємо успішну відповідь
    data = response.json()

    assert "courses" in data
    assert len(data["courses"]) > 0
    
    # Перевірка правильності відображення середнього балу
    assert "statistics" in data
    assert "average_rating" in data["statistics"]
    assert data["statistics"]["average_rating"] == 4.5


def test_access_control_for_transcript(client):
    response = client.get("/transcript")
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert data["courses"][0]["course_name"] == "Test Course 1"
