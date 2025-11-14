from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status

from src.api.repositories.journal_repository import JournalRepository
from src.api.schemas.journal import ExamJournalResponse, StudentInJournal, AttemptInJournal
from src.models.attempts import AttemptStatus

class JournalService:
    def __init__(self):
        self.repo = None

    def _get_overall_status(self, attempts: list) -> AttemptStatus | str:
        """Визначає загальний статус студента на основі його спроб."""
        if not attempts:
            return "not_started" # Якщо спроб немає
        
        # Якщо хоч одна спроба потребує перевірки, це найвищий пріоритет
        if any(att.status == AttemptStatus.submitted for att in attempts):
            return AttemptStatus.submitted
        
        return attempts[0].status

    def get_journal_for_exam(self, db: Session, exam_id: UUID) -> ExamJournalResponse:
        self.repo = JournalRepository(db)

        # 1. Отримуємо іспит та пов'язаний курс
        exam = self.repo.get_exam_with_course(exam_id)
        if not exam or not exam.courses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Іспит або пов'язаний курс не знайдено.")
        
        # 2. Отримуємо студентів курсу та їхні спроби для цього іспиту
        course_id = exam.courses[0].id
        students_with_attempts = self.repo.get_students_with_attempts_for_exam(course_id, exam_id)

        # 3. Форматуємо дані для кожного студента
        students_list = []
        for user in students_with_attempts:

            attempts_for_this_exam = [
                att for att in user.attempts if att.exam_id == exam_id
            ]
            
            # Сортуємо спроби за номером у зворотному порядку
            sorted_attempts = sorted(
                attempts_for_this_exam, 
                key=lambda a: a.started_at,
                reverse=True
            )

            max_grade = None
            if sorted_attempts:
                # Знаходимо максимальний бал серед оцінених спроб
                graded_attempts = [att for att in sorted_attempts if att.earned_points is not None]
                if graded_attempts:
                    max_grade = max(att.earned_points for att in graded_attempts)

            student_data = StudentInJournal(
                id=user.id,
                full_name=f"{user.last_name} {user.first_name} {user.patronymic or ''}".strip(),
                attempts_count=len(sorted_attempts),
                max_grade=max_grade,
                overall_status=self._get_overall_status(sorted_attempts),
                attempts=[
                    AttemptInJournal(
                        id=att.id,
                        attempt_number=idx + 1,
                        earned_points=att.earned_points,
                        time_spent_minutes=att.time_spent_seconds // 60 if att.time_spent_seconds else None,
                        status=att.status
                    ) for idx, att in enumerate(reversed(sorted_attempts)) 
                ]
            )
            students_list.append(student_data)

        # 4. Повертаємо фінальну відповідь
        return ExamJournalResponse(
            exam_id=exam.id,
            exam_name=exam.title,
            max_attempts=exam.max_attempts,
            students=students_list
        )

    def get_exam_statistics_for_course(self, db: Session, course_id: UUID):
        journal_repo = JournalRepository(db)
        
        exams = journal_repo.get_exams_for_course(course_id)
        statistics = []

        for exam in exams:
            attempts = journal_repo.get_attempts_for_exam(exam.id)
            students = []
            for student in attempts:
                max_grade = max(attempt.earned_points for attempt in student.attempts if attempt.earned_points is not None)
                students.append({
                    'student_id': student.id,
                    'name': student.name,
                    'max_grade': max_grade,
                    'attempts': len(student.attempts)
                })
            statistics.append({
                'exam_id': exam.id,
                'exam_name': exam.title,
                'students': students
            })
        
        return statistics