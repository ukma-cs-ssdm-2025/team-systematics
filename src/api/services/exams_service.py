from sqlalchemy.orm import Session
from uuid import UUID
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.courses_repository import CoursesRepository
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, ExamsPage, CourseExamsPage, ExamInList
from src.api.schemas.attempts import AttemptStartRequest, Attempt
from .courses_service import CoursesService
from src.api.errors.app_errors import NotFoundError, ConflictError
from datetime import datetime, timezone

EXAM_NOT_FOUND_MESSAGE = "Exam not found"

class ExamsService:
    def list(self, db: Session, user_id: UUID, limit: int, offset: int):
        """
        Завжди повертає персоналізований список іспитів для користувача.
        """
        repo = ExamsRepository(db)
        items_with_status, _ = repo.list(user_id=user_id, limit=limit, offset=offset)
        
        now = datetime.now(timezone.utc)
        future_or_active = []
        completed_by_user = []

        for exam_model, user_attempts_count in items_with_status:
            exam_schema = Exam.model_validate(exam_model)

            if user_attempts_count >= exam_schema.max_attempts:
                completed_by_user.append(exam_schema)
            
            elif exam_schema.end_at > now:
                future_or_active.append(exam_schema)

        return {"future": future_or_active, "completed": completed_by_user}

    def get(self, db: Session, exam_id: UUID) -> Exam:
        repo = ExamsRepository(db)
        exam = repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)
        return exam

    # --- Question & Option operations for teachers ---
    def create_question(self, db: Session, exam_id: UUID, payload) -> object:
        repo = ExamsRepository(db)
        # verify exam exists
        exam = repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)
        return repo.create_question(exam_id, payload)

    def update_question(self, db: Session, question_id: UUID, patch: dict) -> object:
        repo = ExamsRepository(db)
        updated = repo.update_question(question_id, patch)
        if not updated:
            raise NotFoundError("Question not found")
        return updated

    def delete_question(self, db: Session, question_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete_question(question_id)
        if not ok:
            raise NotFoundError("Question not found")

    def create_option(self, db: Session, question_id: UUID, payload) -> object:
        repo = ExamsRepository(db)
        return repo.create_option(question_id, payload)

    def update_option(self, db: Session, option_id: UUID, patch: dict) -> object:
        repo = ExamsRepository(db)
        updated = repo.update_option(option_id, patch)
        if not updated:
            raise NotFoundError("Option not found")
        return updated

    def delete_option(self, db: Session, option_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete_option(option_id)
        if not ok:
            raise NotFoundError("Option not found")

    def create(self, db: Session, payload: ExamCreate, owner_id: UUID) -> Exam:
        repo = ExamsRepository(db)
        # Встановлюємо owner_id з параметра (якщо не встановлено в payload)
        if not payload.owner_id:
            payload.owner_id = owner_id
        return repo.create(payload)
    
    def link_to_course(self, db: Session, exam_id: UUID, course_id: UUID) -> None:
        """Зв'язує екзамен з курсом"""
        repo = ExamsRepository(db)
        repo.link_to_course(exam_id, course_id)

    def update(self, db: Session, exam_id: UUID, patch: ExamUpdate) -> Exam:
        repo = ExamsRepository(db)
        updated = repo.update(exam_id, patch)
        if not updated:
            raise NotFoundError("Exam not found for update")
        return updated

    def delete(self, db: Session, exam_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete(exam_id)
        if not ok:
            raise NotFoundError("Exam not found for delete")

    def start_attempt(self, db: Session, exam_id: UUID, user_id: UUID) -> Attempt:
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)

        attempts_repo = AttemptsRepository(db)
        
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)

        user_attempts_count = attempts_repo.get_user_attempt_count(
            user_id=user_id,
            exam_id=exam_id
        )
        # Перевіряємо, чи не перевищено ліміт спроб
        if user_attempts_count >= exam.max_attempts:
            raise ConflictError(f"Maximum number of attempts ({exam.max_attempts}) reached for this exam.")

        return attempts_repo.create_attempt(
            exam_id=exam_id,
            user_id=user_id,
            duration_minutes=exam.duration_minutes
        )
    
    def get_exams_for_course(self, db: Session, course_id: UUID) -> CourseExamsPage:
        course_repo = CoursesRepository(db)
        course = course_repo.get(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не знайдено.")
        
        total_students = course_repo.get_student_count(course_id)

        exams_repo = ExamsRepository(db)
        exam_stats = exams_repo.get_exams_stats_for_course(course_id)

        exams_list = []
        for exam, q_count, s_completed, avg_grade, p_reviews in exam_stats:
            exams_list.append(
                ExamInList(
                    id=exam.id,
                    title=exam.title,
                    status=exam.status,
                    questions_count=q_count or 0,
                    students_completed=f"{s_completed or 0} / {total_students}",
                    average_grade=avg_grade if avg_grade else None,
                    pending_reviews=p_reviews or 0
                )
            )

        return CourseExamsPage(
            course_id=course.id,
            course_name=course.name,
            exams=exams_list
        )
    