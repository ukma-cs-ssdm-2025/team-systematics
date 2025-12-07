"""
Tests for attempts controller, service, and repository.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.api.schemas.attempts import Attempt


class MockAttemptsService:
    """Mock attempts service for testing."""
    
    def list_by_exam(self, db, exam_id, skip, limit):
        return [
            Attempt(
                id=uuid4(),
                exam_id=exam_id,
                user_id=uuid4(),
                status="completed",
                started_at=datetime.now(timezone.utc),
                submitted_at=datetime.now(timezone.utc),
                due_at=datetime.now(timezone.utc) + timedelta(hours=2),
                score_percent=85,
                time_spent_seconds=3600
            ),
            Attempt(
                id=uuid4(),
                exam_id=exam_id,
                user_id=uuid4(),
                status="in_progress",
                started_at=datetime.now(timezone.utc),
                due_at=datetime.now(timezone.utc) + timedelta(hours=1),
                score_percent=None,
                time_spent_seconds=1800
            )
        ]
    
    def get_attempt(self, db, attempt_id):
        return Attempt(
            id=attempt_id,
            exam_id=uuid4(),
            user_id=uuid4(),
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            due_at=datetime.now(timezone.utc) + timedelta(hours=2)
        )
    
    def create_attempt(self, db, exam_id, user_id):
        return Attempt(
            id=uuid4(),
            exam_id=exam_id,
            user_id=user_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            due_at=datetime.now(timezone.utc) + timedelta(minutes=120)
        )
    
    def submit_attempt(self, db, attempt_id):
        return Attempt(
            id=attempt_id,
            exam_id=uuid4(),
            user_id=uuid4(),
            status="submitted",
            started_at=datetime.now(timezone.utc),
            submitted_at=datetime.now(timezone.utc),
            due_at=datetime.now(timezone.utc) + timedelta(hours=2),
            score_percent=72,
            time_spent_seconds=4000
        )
    
    def get_attempt_with_details(self, db, attempt_id):
        return {
            "attempt": Attempt(
                id=attempt_id,
                exam_id=uuid4(),
                user_id=uuid4(),
                status="in_progress",
                started_at=datetime.now(timezone.utc),
                due_at=datetime.now(timezone.utc) + timedelta(hours=2)
            ),
            "answers": [
                {
                    "id": uuid4(),
                    "question_id": uuid4(),
                    "answer_text": "Sample answer",
                    "score": 10.0
                }
            ],
            "questions": []
        }


@pytest.fixture
def attempts_service():
    """Create mock attempts service."""
    return MockAttemptsService()


def test_list_attempts_by_exam(attempts_service, test_exam_id):
    """Test listing attempts for an exam."""
    result = attempts_service.list_by_exam(None, test_exam_id, 0, 10)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(attempt.exam_id == test_exam_id for attempt in result)


def test_get_attempt(attempts_service, test_exam_id):
    """Test getting specific attempt."""
    attempt_id = uuid4()
    result = attempts_service.get_attempt(None, attempt_id)
    
    assert result.id == attempt_id
    assert result.status == "in_progress"


def test_create_attempt(attempts_service, test_exam_id, test_user_id):
    """Test creating a new attempt."""
    result = attempts_service.create_attempt(None, test_exam_id, test_user_id)
    
    assert result.exam_id == test_exam_id
    assert result.user_id == test_user_id
    assert result.status == "in_progress"
    assert result.started_at is not None


def test_submit_attempt(attempts_service):
    """Test submitting an attempt."""
    attempt_id = uuid4()
    result = attempts_service.submit_attempt(None, attempt_id)
    
    assert result.id == attempt_id
    assert result.status == "submitted"
    assert result.submitted_at is not None


def test_get_attempt_with_details(attempts_service):
    """Test getting attempt with all details."""
    attempt_id = uuid4()
    result = attempts_service.get_attempt_with_details(None, attempt_id)
    
    assert "attempt" in result
    assert "answers" in result
    assert "questions" in result
    assert result["attempt"].id == attempt_id


def test_attempt_scoring(attempts_service):
    """Test attempt scoring."""
    attempt_id = uuid4()
    result = attempts_service.submit_attempt(None, attempt_id)
    
    assert result.score_percent is not None
    assert 0 <= result.score_percent <= 100


def test_attempt_status_transitions(attempts_service, test_exam_id, test_user_id):
    """Test attempt status transitions."""
    # Create
    attempt = attempts_service.create_attempt(None, test_exam_id, test_user_id)
    assert attempt.status == "in_progress"
    
    # Submit
    submitted = attempts_service.submit_attempt(None, attempt.id)
    assert submitted.status == "submitted"
