from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from src.models.exams import Exam
from src.models.attempts import Attempt
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam

class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_exams_for_student(self, user_id: UUID) -> List[Exam]:
        """
        Повертає список іспитів лише з тих курсів, на які записаний
        вказаний студент.
        """
        query = self.db.query(Exam).join(
            CourseExam, Exam.id == CourseExam.exam_id
        ).join(
            Course, CourseExam.course_id == Course.id
        ).join(
            CourseEnrollment, Course.id == CourseEnrollment.course_id
        ).filter(
            CourseEnrollment.user_id == user_id
        )
        
        return query.all()

    def get_all_attempts_by_user(self, user_id: UUID) -> List[Attempt]:
        """
        Завантажує всі спроби для конкретного користувача.
        """
        return self.db.query(Attempt).filter(Attempt.user_id == user_id).all()