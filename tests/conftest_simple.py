"""
Simplified pytest fixtures for tests using mocks only.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


# Simple test data fixtures (no DB needed)
@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def test_exam_id():
    """Generate a test exam ID."""
    return uuid4()


@pytest.fixture
def test_course_id():
    """Generate a test course ID."""
    return uuid4()


@pytest.fixture
def test_question_id():
    """Generate a test question ID."""
    return uuid4()


@pytest.fixture
def test_attempt_id():
    """Generate a test attempt ID."""
    return uuid4()
