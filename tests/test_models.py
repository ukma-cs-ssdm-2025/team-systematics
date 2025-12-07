"""
Tests for database models validation and relationships.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.models.users import User
from src.models.user_roles import UserRole
from src.models.attempts import Attempt
from src.models.exams import Exam
from src.models.courses import Course
from src.models.majors import Major
from src.models.course_exams import CourseExam
from src.models.user_majors import UserMajor
from src.models.roles import Role


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self):
        """Test creating a user model instance."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_pwd_123"
        )
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.hashed_password == "hashed_pwd_123"
    
    def test_user_with_patronymic(self):
        """Test user model with patronymic."""
        user = User(
            id=uuid4(),
            email="user@test.com",
            first_name="John",
            last_name="Doe",
            patronymic="Michael",
            hashed_password="hash"
        )
        
        assert user.email == "user@test.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.patronymic == "Michael"
    
    def test_user_email_format(self):
        """Test user email is stored correctly."""
        email = "user@example.com"
        user = User(
            id=uuid4(),
            email=email,
            first_name="Test",
            last_name="User",
            hashed_password="hash"
        )
        
        assert user.email == email
        assert "@" in user.email


class TestExamModel:
    """Tests for Exam model."""
    
    def test_exam_creation(self):
        """Test creating an exam model instance."""
        now = datetime.now(timezone.utc)
        exam = Exam(
            id=uuid4(),
            title="Test Exam",
            start_at=now,
            end_at=now + timedelta(hours=2),
            duration_minutes=120,
            owner_id=uuid4()
        )
        
        assert exam.title == "Test Exam"
        assert exam.duration_minutes == 120
        assert exam.start_at == now
    
    def test_exam_with_defaults(self):
        """Test exam model default values."""
        now = datetime.now(timezone.utc)
        exam = Exam(
            id=uuid4(),
            title="Exam",
            start_at=now,
            end_at=now + timedelta(hours=1),
            owner_id=uuid4()
        )
        
        assert exam.title == "Exam"
        assert exam.start_at < exam.end_at
    
    def test_exam_time_validity(self):
        """Test exam time validity - end after start."""
        now = datetime.now(timezone.utc)
        start = now
        end = now + timedelta(hours=2)
        
        exam = Exam(
            id=uuid4(),
            title="Valid Exam",
            start_at=start,
            end_at=end,
            owner_id=uuid4()
        )
        
        assert exam.start_at < exam.end_at


class TestCourseModel:
    """Tests for Course model."""
    
    def test_course_creation(self):
        """Test creating a course model instance."""
        course = Course(
            id=uuid4(),
            name="Python Basics",
            code="CS101",
            owner_id=uuid4()
        )
        
        assert course.name == "Python Basics"
        assert course.code == "CS101"
    
    def test_course_with_description(self):
        """Test course with description."""
        course = Course(
            id=uuid4(),
            name="Advanced Python",
            code="CS201",
            description="Learn advanced Python concepts",
            owner_id=uuid4()
        )
        
        assert course.name == "Advanced Python"
        assert course.code == "CS201"
        assert course.description == "Learn advanced Python concepts"


class TestMajorModel:
    """Tests for Major model."""
    
    def test_major_creation(self):
        """Test creating a major model instance."""
        major = Major(
            id=1,
            name="Computer Science"
        )
        
        assert major.name == "Computer Science"
        assert major.id == 1
    
    def test_major_unique_name(self):
        """Test major with unique name."""
        major = Major(
            id=2,
            name="Software Engineering"
        )
        
        assert major.name == "Software Engineering"
        assert major.id == 2


class TestRoleModel:
    """Tests for Role model."""
    
    def test_role_creation(self):
        """Test creating a role model instance."""
        role = Role(
            id=1,
            name="teacher"
        )
        
        assert role.name == "teacher"
        assert role.id == 1
    
    def test_different_roles(self):
        """Test different role types."""
        roles_data = [
            (1, "student"),
            (2, "teacher"),
            (3, "admin")
        ]
        
        for role_id, role_name in roles_data:
            role = Role(id=role_id, name=role_name)
            assert role.name == role_name
            assert role.id == role_id


class TestUserRoleModel:
    """Tests for UserRole model."""
    
    def test_user_role_creation(self):
        """Test creating a user role relationship."""
        user_id = uuid4()
        role_id = 1
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id
        )
        
        assert user_role.user_id == user_id
        assert user_role.role_id == role_id
    
    def test_user_multiple_roles(self):
        """Test that user can have multiple roles."""
        user_id = uuid4()
        
        student_role = UserRole(
            user_id=user_id,
            role_id=1
        )
        
        teacher_role = UserRole(
            user_id=user_id,
            role_id=2
        )
        
        assert student_role.user_id == teacher_role.user_id
        assert student_role.role_id != teacher_role.role_id


class TestAttemptModel:
    """Tests for Attempt model."""
    
    def test_attempt_creation(self):
        """Test creating an attempt model instance."""
        now = datetime.now(timezone.utc)
        attempt = Attempt(
            id=uuid4(),
            exam_id=uuid4(),
            user_id=uuid4(),
            started_at=now,
            due_at=now + timedelta(hours=2)
        )
        
        assert attempt.exam_id is not None
        assert attempt.user_id is not None
        assert attempt.started_at == now
    
    def test_attempt_with_score(self):
        """Test attempt with earned points."""
        now = datetime.now(timezone.utc)
        attempt = Attempt(
            id=uuid4(),
            exam_id=uuid4(),
            user_id=uuid4(),
            started_at=now,
            due_at=now + timedelta(hours=2),
            earned_points=85.5
        )
        
        assert attempt.earned_points == 85.5


class TestExamRelationships:
    """Tests for model relationships."""
    
    def test_exam_with_owner(self):
        """Test exam has owner reference."""
        owner_id = uuid4()
        now = datetime.now(timezone.utc)
        
        exam = Exam(
            id=uuid4(),
            title="Course Exam",
            start_at=now,
            end_at=now + timedelta(hours=1),
            owner_id=owner_id
        )
        
        assert exam.owner_id == owner_id
        assert exam.title == "Course Exam"
    
    def test_user_major_relationship(self):
        """Test user-major relationship structure."""
        user_id = uuid4()
        major_id = 1
        
        user_major = UserMajor(
            user_id=user_id,
            major_id=major_id
        )
        
        assert user_major.user_id == user_id
        assert user_major.major_id == major_id
    
    def test_course_exam_relationship(self):
        """Test course-exam relationship structure."""
        course_id = uuid4()
        exam_id = uuid4()
        
        course_exam = CourseExam(
            course_id=course_id,
            exam_id=exam_id
        )
        
        assert course_exam.course_id == course_id
        assert course_exam.exam_id == exam_id
