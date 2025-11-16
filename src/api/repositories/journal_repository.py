from sqlalchemy.orm import Session, joinedload, contains_eager, selectinload
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from src.models.users import User
from src.models.exams import Exam
from src.models.attempts import Attempt
from src.models.courses import Course, CourseEnrollment
from src.models.user_roles import UserRole
from src.models.roles import Role
from src.models.course_exams import CourseExam

class JournalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_exam_with_course(self, exam_id: UUID) -> Optional[Exam]:
        """Знаходить іспит і його перший пов'язаний курс."""
        return self.db.query(Exam).options(
            joinedload(Exam.courses)
        ).filter(Exam.id == exam_id).first()

    def get_students_with_attempts_for_exam(self, course_id: UUID, exam_id: UUID) -> List[User]:
        """
        Знаходить всіх студентів курсу та їхні спроби для конкретного іспиту.
        Студенти без спроб також включаються в результат.
        Фільтрує тільки користувачів з роллю 'student'.
        """
        return (
            self.db.query(User)
            .join(CourseEnrollment, User.id == CourseEnrollment.user_id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .outerjoin(
                Attempt,
                (User.id == Attempt.user_id) & (Attempt.exam_id == exam_id)
            )
            .filter(
                CourseEnrollment.course_id == course_id,
                Role.name == 'student'
            )
            .options(
                contains_eager(User.attempts)
            )
            .order_by(User.last_name, User.first_name)
            .all()
        )

    def get_exams_for_course(self, course_id: UUID) -> List[Exam]:
        """Отримує список іспитів для курсу"""
        return (
            self.db.query(Exam)
            .join(CourseExam, Exam.id == CourseExam.exam_id)
            .filter(CourseExam.course_id == course_id)
            .all()
        )

    def get_attempts_for_exam(self, exam_id: UUID) -> List[User]:
        """
        Отримує список студентів з їхніми спробами для конкретного іспиту.
        Повертає список користувачів з завантаженими спробами тільки для цього іспиту.
        """
        users = (
            self.db.query(User)
            .join(Attempt, User.id == Attempt.user_id)
            .filter(Attempt.exam_id == exam_id)
            .options(
                selectinload(User.attempts)
            )
            .distinct()
            .all()
        )
        
        # Фільтруємо спроби для кожного користувача, щоб залишити тільки спроби для цього іспиту
        for user in users:
            user.attempts = [attempt for attempt in user.attempts if attempt.exam_id == exam_id]
        
        return users