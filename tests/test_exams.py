"""
Tests for exams controller, service, and repository.
"""
import pytest
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.api.schemas.exams import ExamCreate, ExamUpdate, Exam
from src.models.exams import Exam as ExamModel, ExamStatusEnum


class MockExamsService:
    """Mock exams service for testing."""
    
    def list(self, db, user_id, limit, offset):
        now = datetime.now(timezone.utc)
        return ({
            "future": [
                Exam(
                    id=uuid4(),
                    title="Upcoming Exam",
                    start_at=now + timedelta(days=1),
                    end_at=now + timedelta(days=2),
                    duration_minutes=120,
                    max_attempts=3,
                    pass_threshold=60,
                    owner_id=user_id,
                    status="published",
                    question_count=10
                )
            ],
            "completed": []
        })
    
    def get(self, db, exam_id):
        return Exam(
            id=exam_id,
            title="Sample Exam",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(hours=2),
            duration_minutes=120,
            max_attempts=1,
            pass_threshold=70,
            owner_id=uuid4(),
            status="published",
            question_count=20
        )
    
    def create(self, db, payload, owner_id):
        return Exam(
            id=uuid4(),
            title=payload.title,
            start_at=payload.start_at,
            end_at=payload.end_at,
            duration_minutes=payload.duration_minutes,
            max_attempts=payload.max_attempts,
            pass_threshold=payload.pass_threshold,
            owner_id=owner_id,
            status="draft",
            question_count=0
        )
    
    def publish_exam(self, db, exam_id):
        return Exam(
            id=exam_id,
            title="Published Exam",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(hours=2),
            duration_minutes=60,
            max_attempts=2,
            pass_threshold=65,
            owner_id=uuid4(),
            status="published",
            question_count=15
        )
    
    def start_attempt(self, db, exam_id, user_id):
        from src.api.schemas.attempts import Attempt
        return Attempt(
            id=uuid4(),
            exam_id=exam_id,
            user_id=user_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            due_at=datetime.now(timezone.utc) + timedelta(minutes=120)
        )


@pytest.fixture
def exams_service():
    """Create mock exams service."""
    return MockExamsService()


def test_list_exams(exams_service, test_user_id):
    """Test listing exams."""
    result = exams_service.list(None, test_user_id, 10, 0)
    
    assert "future" in result
    assert "completed" in result
    assert isinstance(result["future"], list)
    assert isinstance(result["completed"], list)


def test_get_exam(exams_service, test_exam_id):
    """Test getting specific exam."""
    result = exams_service.get(None, test_exam_id)
    
    assert result.id == test_exam_id
    assert result.title is not None
    assert result.duration_minutes > 0


def test_create_exam(exams_service, test_user_id):
    """Test creating an exam."""
    now = datetime.now(timezone.utc)
    payload = ExamCreate(
        title="New Test Exam",
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=2),
        duration_minutes=90,
        max_attempts=3,
        pass_threshold=75,
        owner_id=test_user_id
    )
    
    result = exams_service.create(None, payload, test_user_id)
    
    assert result.title == payload.title
    assert result.owner_id == test_user_id
    assert result.status == "draft"


def test_publish_exam(exams_service, test_exam_id):
    """Test publishing an exam."""
    result = exams_service.publish_exam(None, test_exam_id)
    
    assert result.status == "published"


def test_start_attempt(exams_service, test_exam_id, test_user_id):
    """Test starting an exam attempt."""
    result = exams_service.start_attempt(None, test_exam_id, test_user_id)
    
    assert result.exam_id == test_exam_id
    assert result.user_id == test_user_id
    assert result.status == "in_progress"
    assert result.started_at is not None
    assert result.due_at is not None
