from unittest.mock import MagicMock
import pytest
from uuid import uuid4
from src.api.repositories.courses_repository import CoursesRepository
from src.models.courses import Course, CourseEnrollment
from src.api.schemas.courses import CourseCreate, CourseUpdate
from sqlalchemy.orm import Session
from typing import List, Tuple


@pytest.fixture
def mock_db():
    """Мокування об'єкта бази даних для тестів"""
    db = MagicMock(Session)
    return db

@pytest.fixture
def repo(mock_db):
    """Мок репозиторію для курсів"""
    return CoursesRepository(db=mock_db)


def test_list_courses(repo, mock_db):
    mock_db.query.return_value.count.return_value = 1
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [Course(id=uuid4(), title="Test Course", description="Test Description")]

    items, total = repo.list(limit=10, offset=0)
    
    assert total == 1
    assert len(items) == 1
    assert items[0].title == "Test Course"


def test_get_course(repo, mock_db):
    course_id = uuid4()
    mock_db.query.return_value.filter.return_value.first.return_value = Course(id=course_id, title="Test Course", description="Test Description")
    
    course = repo.get(course_id)
    
    assert course is not None
    assert course.id == course_id
    assert course.title == "Test Course"


def test_create_course(repo, mock_db):
    course_data = CourseCreate(title="Test Course", description="Test Description")
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    course = repo.create(course_data)

    assert course.title == "Test Course"
    assert course.description == "Test Description"


def test_update_course(repo, mock_db):
    course_id = uuid4()
    patch_data = CourseUpdate(title="Updated Course", description="Updated Description")
    mock_db.query.return_value.filter.return_value.first.return_value = Course(id=course_id, title="Test Course", description="Test Description")
    
    updated_course = repo.update(course_id, patch_data)
    
    assert updated_course.title == "Updated Course"
    assert updated_course.description == "Updated Description"


def test_delete_course(repo, mock_db):
    course_id = uuid4()
    mock_db.query.return_value.filter.return_value.first.return_value = Course(id=course_id, title="Test Course", description="Test Description")
    
    repo.delete(course_id)

    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()


def test_list_my_courses(repo, mock_db):
    user_id = uuid4()
    mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 1
    mock_db.query.return_value.join.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [Course(id=uuid4(), title="Test Course", description="Test Description")]

    items, total = repo.list_my(user_id, limit=10, offset=0)
    
    assert total == 1
    assert len(items) == 1
    assert items[0].title == "Test Course"
