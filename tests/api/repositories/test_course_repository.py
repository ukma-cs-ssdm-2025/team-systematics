from unittest.mock import MagicMock
import pytest
from uuid import uuid4
from src.api.repositories.courses_repository import CoursesRepository
from src.models.courses import Course
from src.api.schemas.courses import CourseCreate, CourseUpdate
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    """Mocking the database object for tests"""
    db = MagicMock(Session)
    return db

@pytest.fixture
def repo(mock_db):
    """Mock repository for courses"""
    return CoursesRepository(db=mock_db)


# Test for listing courses
def test_list_courses(repo, mock_db):
    # The repository builds a query with outerjoin().outerjoin().add_columns() and then calls
    # count() and order_by(...).limit(...).offset(...).all() on that result.
    base_query = mock_db.query.return_value
    after_joins = base_query.outerjoin.return_value.outerjoin.return_value
    final_query = after_joins.add_columns.return_value

    final_query.count.return_value = 1
    final_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
        (
            Course(id=uuid4(), name="Test Course", description="Test Description", code="CS101"),
            30,
            3,
            False
        )
    ]

    items, total = repo.list(current_user_id=None, limit=10, offset=0)

    assert total == 1
    assert len(items) == 1
    assert items[0]["name"] == "Test Course"


# Test for creating a course
def test_create_course(repo, mock_db):
    course_data = CourseCreate(name="Test Course", description="Test Description", code="CS101")
    
    # Mock the DB methods
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    course = repo.create(course_data)

    # Check that the course creation is correct
    assert course.name == "Test Course"
    assert course.description == "Test Description"
    assert course.code == "CS101"


# Test for updating a course
def test_update_course(repo, mock_db):
    course_id = uuid4()
    patch_data = CourseUpdate(name="Updated Course", description="Updated Description", code="CS102")

    mock_db.query.return_value.filter.return_value.first.return_value = Course(
        id=course_id, name="Test Course", description="Test Description", code="CS101"
    )

    updated_course = repo.update(course_id, patch_data)

    assert updated_course.name == "Updated Course"
    assert updated_course.description == "Updated Description"
    assert updated_course.code == "CS102"


# Test for deleting a course
def test_delete_course(repo, mock_db):
    course_id = uuid4()
    mock_db.query.return_value.filter.return_value.first.return_value = Course(
        id=course_id, name="Test Course", description="Test Description", code="CS101"
    )
    
    repo.delete(course_id)

    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()
