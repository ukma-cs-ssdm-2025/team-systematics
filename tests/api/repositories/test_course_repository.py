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
    from src.models.users import User
    
    # Mock subqueries - these are created first but we don't need to fully mock them
    # Just ensure db.query() can be called multiple times
    subquery_mock = MagicMock()
    subquery_mock.subquery.return_value = MagicMock()  # Mock subquery object
    
    # Mock the main query chain
    base_query = MagicMock()
    after_first_join = MagicMock()
    after_second_join = MagicMock()
    after_add_columns = MagicMock()
    after_owner_join = MagicMock()
    final_query = MagicMock()
    
    # Set up the chain
    base_query.outerjoin.return_value = after_first_join
    after_first_join.outerjoin.return_value = after_second_join
    after_second_join.add_columns.return_value = after_add_columns
    after_add_columns.outerjoin.return_value = after_owner_join
    after_owner_join.add_columns.return_value = final_query
    
    # Mock db.query() to return subquery_mock for subqueries and base_query for main query
    # First two calls are for subqueries, third call is main query with Course
    call_count = [0]  # Use list to allow modification in nested function
    def query_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            return subquery_mock
        else:
            return base_query
    
    mock_db.query.side_effect = query_side_effect
    
    # Mock owner user
    mock_owner = MagicMock(spec=User)
    mock_owner.id = uuid4()
    mock_owner.first_name = "John"
    mock_owner.last_name = "Doe"
    
    # Mock the result - includes owner as 5th element when include_owner=True
    course = Course(id=uuid4(), name="Test Course", description="Test Description", code="CS101")
    order_by_mock = MagicMock()
    final_query.order_by.return_value = order_by_mock
    order_by_mock.all.return_value = [
        (
            course,
            30,  # student_count
            3,   # exam_count
            False,  # is_enrolled
            mock_owner  # owner
        )
    ]

    items, total = repo.list(current_user_id=None, limit=10, offset=0)

    assert total == 1
    assert len(items) == 1
    assert items[0]["name"] == "Test Course"


# Test for creating a course
def test_create_course(repo, mock_db):
    course_data = CourseCreate(name="Test Course", description="Test Description", code="CS101")
    owner_id = uuid4()

    # Mock the DB methods
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    course = repo.create(course_data, owner_id=owner_id)

    assert course.name == "Test Course"
    assert course.description == "Test Description"
    assert course.code == "CS101"
    assert course.owner_id == owner_id


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
