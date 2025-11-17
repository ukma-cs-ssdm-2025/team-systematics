import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from uuid import uuid4

from src.api.controllers.exams_controller import ExamsController
from src.api.controllers.versioning import require_api_version
from src.api.database import get_db
from src.utils.auth import get_current_user_with_role
from types import SimpleNamespace


def test_get_exams_db_failure_returns_500():
    """Simulate a DB failure by making the `get_db` dependency raise an exception."""

    class DummyService:
        @staticmethod
        def list(db, user_id, limit, offset):
            return {"future": [], "completed": []}

    app = FastAPI()
    app.dependency_overrides[require_api_version] = lambda: None
    controller = ExamsController(DummyService())
    app.include_router(controller.router)

    # Simulate DB crash
    def _broken_db():
        try:
            yield None
            raise RuntimeError("DB connection failed")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            ) from e

    app.dependency_overrides[get_db] = _broken_db
    dummy_user = SimpleNamespace(id=uuid4(), role='student')
    app.dependency_overrides[get_current_user_with_role] = lambda: dummy_user

    client = TestClient(app)

    response = client.get("/exams")
    assert response.status_code == 500
    error_response = response.json()
    assert "detail" in error_response
    assert error_response["detail"]["code"] == "INTERNAL_ERROR"
    assert "DB connection failed" in error_response["detail"]["message"]
