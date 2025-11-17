from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from uuid import uuid4

from src.api.controllers.courses_controller import CoursesController
from src.api.database import get_db
from src.api.schemas.courses import CourseCreate, Course, CoursesPage
from src.api.services.courses_service import CoursesService
from src.api.controllers.versioning import require_api_version
from src.api.schemas.auth import UserResponse
from src.utils.auth import get_current_user

@pytest.fixture
def client():
    app = FastAPI()

    class MockCoursesService:
        @staticmethod
        def list(db, user_id, limit, offset):
            return [
                Course(
                    id=1,
                    name="Test Course 1",
                    description="Test Description 1",
                    title="Test Course 1 Title"
                )
            ], 1

        @staticmethod
        def create(db, payload: CourseCreate):
            return Course(
                id=uuid4(),
                name=payload.name,
                description=payload.description,
                title=payload.name
            )

        @staticmethod
        def get(db, course_id: int):
            # Повернення конкретного курсу за id
            return Course(
                id=course_id,
                name="Test Course",
                description="Test Course Description",
                title="Test Course Title"
            )
        
    controller = CoursesController(MockCoursesService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_current_user] = lambda: UserResponse(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        roles=["student"],
        user_major="Computer Science"
    )

    app.dependency_overrides[get_db] = _fake_db

    return TestClient(app)


@pytest.fixture
def mock_course():
    return {
        "name": "Test Course",
        "description": "Test Description"
    }


# Тест для створення курсу
def test_create_course(client, mock_course):
    response = client.post("/courses", json=mock_course)

    print(response.json())
    
    data = response.json()

    assert "detail" in data, f"Expected 'detail' key in the response, got: {data}"

