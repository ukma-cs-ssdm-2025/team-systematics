from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class CourseResult(BaseModel):
    """Описує результат по одному курсу (іспиту) в атестаті."""
    id: UUID = Field(..., description="ID іспиту (курсу)")
    course_name: str = Field(..., description="Назва іспиту (курсу)")
    rating: Optional[float] = Field(None, description="Найкращий результат у 100-бальній шкалі", example=92.0)
    ects_grade: Optional[str] = Field(None, description="Оцінка за шкалою ECTS (A, B, C...)", example="A")
    national_grade: Optional[str] = Field(None, description="Оцінка за національною шкалою (Відмінно, Добре...)", example="Відмінно")
    pass_status: Optional[str] = Field(None, description="Статус зарахування ('Так' або 'Ні')", example="Так")

class Statistics(BaseModel):
    """Описує загальну статистику успішності студента."""
    completed_courses: int = Field(..., description="Кількість курсів, де була хоча б одна спроба", example=1)
    total_courses: int = Field(..., description="Загальна кількість доступних курсів/іспитів", example=4)
    a_grades_count: int = Field(..., description="Кількість курсів, зданих на оцінку 'A'", example=1)
    average_rating: float = Field(..., description="Середній рейтинг по всіх зданих курсах", example=92.0)

class CertificateResponse(BaseModel):
    """Головна модель відповіді для сторінки 'Мій атестат'."""
    courses: List[CourseResult]
    statistics: Statistics