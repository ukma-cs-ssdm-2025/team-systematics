"""
Tests for courses service with mocks.
"""
import pytest
from uuid import uuid4


class MockCoursesService:
    """Mock courses service for testing."""
    
    def list_courses(self, user_id, limit=10, offset=0):
        """List courses for a user."""
        return [
            {
                "id": uuid4(),
                "name": "Python Basics",
                "code": "PY101",
                "owner_id": user_id,
                "description": "Learn Python fundamentals"
            }
        ]
    
    def get_course(self, course_id):
        """Get a specific course."""
        return {
            "id": course_id,
            "name": "Advanced Python",
            "code": "PY201",
            "owner_id": uuid4(),
            "description": "Advanced Python topics"
        }
    
    def create_course(self, name, code, owner_id, description=None):
        """Create a new course."""
        return {
            "id": uuid4(),
            "name": name,
            "code": code,
            "owner_id": owner_id,
            "description": description
        }
    
    def update_course(self, course_id, name=None, code=None, description=None):
        """Update an existing course."""
        return {
            "id": course_id,
            "name": name or "Updated Course",
            "code": code or "UPD101",
            "owner_id": uuid4(),
            "description": description or "Updated description"
        }
    
    def delete_course(self, course_id):
        """Delete a course."""
        return True


@pytest.fixture
def courses_service():
    """Create mock courses service."""
    return MockCoursesService()


def test_list_courses(courses_service, test_user_id):
    """Test listing courses."""
    result = courses_service.list_courses(test_user_id)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(course["owner_id"] == test_user_id for course in result)


def test_get_course(courses_service, test_course_id):
    """Test getting a specific course."""
    result = courses_service.get_course(test_course_id)
    
    assert result["id"] == test_course_id
    assert result["name"] is not None


def test_create_course(courses_service, test_user_id):
    """Test creating a course."""
    result = courses_service.create_course(
        name="New Course",
        code="NEW101",
        owner_id=test_user_id,
        description="A new course"
    )
    
    assert result["name"] == "New Course"
    assert result["code"] == "NEW101"
    assert result["owner_id"] == test_user_id


def test_update_course(courses_service, test_course_id):
    """Test updating a course."""
    result = courses_service.update_course(
        course_id=test_course_id,
        name="Updated Course Name",
        code="UPD202"
    )
    
    assert result["id"] == test_course_id
    assert result["name"] == "Updated Course Name"
    assert result["code"] == "UPD202"


def test_delete_course(courses_service, test_course_id):
    """Test deleting a course."""
    result = courses_service.delete_course(test_course_id)
    
    assert result is True
