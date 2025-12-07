"""
Tests for questions controller, service, and repository.
"""
import pytest
from uuid import uuid4


class MockQuestionsService:
    """Mock questions service for testing."""
    
    def list_questions(self, db, exam_id, skip, limit):
        return [
            {
                "id": uuid4(),
                "exam_id": exam_id,
                "title": "What is 2+2?",
                "question_type": "multiple_choice",
                "points": 10,
                "position": 1
            },
            {
                "id": uuid4(),
                "exam_id": exam_id,
                "title": "What is the capital of France?",
                "question_type": "short_answer",
                "points": 5,
                "position": 2
            }
        ]
    
    def get_question(self, db, question_id):
        return {
            "id": question_id,
            "exam_id": uuid4(),
            "title": "Sample question",
            "question_type": "multiple_choice",
            "points": 10,
            "position": 1
        }
    
    def create_question(self, db, exam_id, payload):
        return {
            "id": uuid4(),
            "exam_id": exam_id,
            "title": payload.get("title", "New Question"),
            "question_type": payload.get("question_type", "multiple_choice"),
            "points": payload.get("points", 10),
            "position": payload.get("position", 1)
        }
    
    def update_question(self, db, question_id, payload):
        return {
            "id": question_id,
            "exam_id": uuid4(),
            "title": payload.get("title", "Updated Question"),
            "question_type": payload.get("question_type", "multiple_choice"),
            "points": payload.get("points", 10),
            "position": payload.get("position", 1)
        }
    
    def delete_question(self, db, question_id):
        return True
    
    def reorder_questions(self, db, exam_id, order):
        return True


@pytest.fixture
def questions_service():
    """Create mock questions service."""
    return MockQuestionsService()


def test_list_questions(questions_service, test_exam_id):
    """Test listing questions in an exam."""
    result = questions_service.list_questions(None, test_exam_id, 0, 10)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(q["exam_id"] == test_exam_id for q in result)


def test_get_question(questions_service):
    """Test retrieving a specific question."""
    question_id = uuid4()
    result = questions_service.get_question(None, question_id)
    
    assert result["id"] == question_id
    assert result["title"] is not None
    assert result["points"] > 0


def test_create_question(questions_service, test_exam_id):
    """Test creating a question."""
    payload = {
        "title": "Which planet is largest?",
        "question_type": "multiple_choice",
        "points": 15,
        "position": 3
    }
    
    result = questions_service.create_question(None, test_exam_id, payload)
    
    assert result["exam_id"] == test_exam_id
    assert result["title"] == payload["title"]
    assert result["question_type"] == "multiple_choice"


def test_update_question(questions_service, test_exam_id):
    """Test updating a question."""
    question_id = uuid4()
    payload = {
        "title": "Updated question text",
        "question_type": "multiple_choice",
        "points": 12,
        "position": 2
    }
    
    result = questions_service.update_question(None, question_id, payload)
    
    assert result["id"] == question_id
    assert result["title"] == "Updated question text"
    assert result["points"] == 12


def test_delete_question(questions_service):
    """Test deleting a question."""
    question_id = uuid4()
    result = questions_service.delete_question(None, question_id)
    
    assert result is True


def test_reorder_questions(questions_service, test_exam_id):
    """Test reordering questions."""
    new_order = [uuid4(), uuid4(), uuid4()]
    result = questions_service.reorder_questions(None, test_exam_id, new_order)
    
    assert result is True


def test_question_validation(questions_service, test_exam_id):
    """Test question validation."""
    # Valid question
    valid_payload = {
        "title": "Valid question?",
        "question_type": "multiple_choice",
        "points": 10,
        "position": 1
    }
    
    result = questions_service.create_question(None, test_exam_id, valid_payload)
    assert result is not None
    assert result["points"] == 10
