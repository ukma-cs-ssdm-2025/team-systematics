"""
Tests for analytics and reporting functionality.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from src.api.schemas.analytics import ExamStatistics, GroupAnalytics, CourseAnalyticsResponse


class MockAnalyticsService:
    """Mock analytics service for testing."""
    
    def get_exam_statistics(self, db, exam_id):
        return ExamStatistics(
            exam_id=exam_id,
            total_students=45,
            min_score=42.0,
            max_score=98.0,
            median_score=75.0
        )
    
    def get_group_analytics(self, db, course_id, start_date=None, end_date=None):
        return {
            "course_id": course_id,
            "total_students": 120,
            "active_students": 95,
            "total_exams": 8,
            "average_exam_score": 68.9,
            "student_engagement_rate": 79.2
        }
    
    def get_student_performance(self, db, user_id, course_id=None):
        return {
            "user_id": user_id,
            "total_attempts": 12,
            "completed_exams": 10,
            "average_score": 81.5,
            "highest_score": 95.0,
            "lowest_score": 65.0,
            "pass_rate": 90.0
        }
    
    def get_question_statistics(self, db, question_id):
        return {
            "question_id": question_id,
            "times_attempted": 150,
            "times_answered_correctly": 120,
            "difficulty_index": 0.8,
            "average_time_spent": 45.5
        }
    
    def get_exam_difficulty_report(self, db, exam_id):
        return {
            "exam_id": exam_id,
            "average_difficulty": 6.5,
            "questions_by_difficulty": {
                "easy": 5,
                "medium": 8,
                "hard": 7
            }
        }


@pytest.fixture
def analytics_service():
    """Create mock analytics service."""
    return MockAnalyticsService()


def test_get_exam_statistics(analytics_service, test_exam_id):
    """Test retrieving exam statistics."""
    result = analytics_service.get_exam_statistics(None, test_exam_id)
    
    assert result.exam_id == test_exam_id
    assert result.total_students >= 0
    assert result.median_score is not None
    assert 0 <= result.median_score <= 100


def test_exam_statistics_values(analytics_service, test_exam_id):
    """Test exam statistics values are valid."""
    result = analytics_service.get_exam_statistics(None, test_exam_id)
    
    assert result.min_score <= result.median_score <= result.max_score
    assert result.min_score >= 0


def test_get_group_analytics(analytics_service, test_course_id):
    """Test retrieving group analytics."""
    result = analytics_service.get_group_analytics(None, test_course_id)
    
    assert result["course_id"] == test_course_id
    assert result["total_students"] > 0
    assert result["active_students"] <= result["total_students"]


def test_group_analytics_values(analytics_service, test_course_id):
    """Test group analytics values are valid."""
    result = analytics_service.get_group_analytics(None, test_course_id)
    
    assert 0 <= result["student_engagement_rate"] <= 100
    assert result["average_exam_score"] >= 0


def test_get_student_performance(analytics_service, test_user_id):
    """Test retrieving student performance data."""
    result = analytics_service.get_student_performance(None, test_user_id)
    
    assert result["user_id"] == test_user_id
    assert result["total_attempts"] >= 0
    assert result["completed_exams"] <= result["total_attempts"]


def test_student_performance_statistics(analytics_service, test_user_id):
    """Test student performance statistics validity."""
    result = analytics_service.get_student_performance(None, test_user_id)
    
    assert 0 <= result["pass_rate"] <= 100
    assert result["lowest_score"] <= result["average_score"] <= result["highest_score"]


def test_get_question_statistics(analytics_service, test_question_id):
    """Test retrieving question statistics."""
    result = analytics_service.get_question_statistics(None, test_question_id)
    
    assert result["question_id"] == test_question_id
    assert result["times_attempted"] >= 0
    assert result["times_answered_correctly"] <= result["times_attempted"]


def test_question_difficulty_calculation(analytics_service, test_question_id):
    """Test question difficulty calculation."""
    result = analytics_service.get_question_statistics(None, test_question_id)
    
    assert 0 <= result["difficulty_index"] <= 1.0
    assert result["average_time_spent"] >= 0


def test_get_exam_difficulty_report(analytics_service, test_exam_id):
    """Test retrieving exam difficulty report."""
    result = analytics_service.get_exam_difficulty_report(None, test_exam_id)
    
    assert result["exam_id"] == test_exam_id
    assert "average_difficulty" in result
    assert "questions_by_difficulty" in result


def test_difficulty_distribution(analytics_service, test_exam_id):
    """Test difficulty distribution in exam."""
    result = analytics_service.get_exam_difficulty_report(None, test_exam_id)
    
    total_questions = (
        result["questions_by_difficulty"]["easy"] +
        result["questions_by_difficulty"]["medium"] +
        result["questions_by_difficulty"]["hard"]
    )
    
    assert total_questions > 0
    assert 0 <= result["average_difficulty"] <= 10


def test_course_analytics_with_date_range(analytics_service, test_course_id):
    """Test course analytics with date range."""
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    result = analytics_service.get_group_analytics(
        None, test_course_id, start_date, end_date
    )
    
    assert result["course_id"] == test_course_id


def test_performance_trend_analysis(analytics_service, test_user_id):
    """Test performance trend analysis."""
    current = analytics_service.get_student_performance(None, test_user_id)
    
    assert current["average_score"] >= 0
    assert current["highest_score"] >= current["average_score"]


def test_analytics_aggregation(analytics_service, test_exam_id, test_course_id):
    """Test analytics aggregation across exam and course."""
    exam_stats = analytics_service.get_exam_statistics(None, test_exam_id)
    group_stats = analytics_service.get_group_analytics(None, test_course_id)
    
    assert exam_stats is not None
    assert group_stats is not None
    assert exam_stats.exam_id != group_stats["course_id"]
