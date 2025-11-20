from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class GroupAnalytics(BaseModel):
    exam_id: UUID
    exam_name: str
    course_id: UUID
    course_name: str
    average_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]
    median_score: Optional[float]

class ExamStatistics(BaseModel):
    exam_id: UUID
    min_score: Optional[float]
    max_score: Optional[float]
    median_score: Optional[float]
    total_students: int

class ExamProgress(BaseModel):
    exam_id: UUID
    date: datetime
    average_score: float

class CourseAnalyticsResponse(BaseModel):
    group_stats: List[GroupAnalytics]
    exam_statistics: List[ExamStatistics]

class GroupScoreAnalytics(BaseModel):
    total_students: int
    students_completed: int
    total_attempts: Optional[int] = None  # Загальна кількість спроб (може бути більше за students_completed, якщо дозволено кілька спроб)
    average_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]
    median_score: Optional[float]
    scores: Optional[List[float]] = None  # Бали для гістограми (тільки найкращі спроби кожного студента)
