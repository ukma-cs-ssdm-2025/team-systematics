from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import uuid as uuid_lib
from src.api.repositories.exams_repository import ExamsRepository
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.courses_repository import CoursesRepository
from src.api.schemas.exams import Exam, ExamCreate, ExamUpdate, CourseExamsPage, ExamInList, ExamWithQuestions
from src.api.schemas.attempts import Attempt
from src.api.errors.app_errors import NotFoundError, ConflictError
from datetime import datetime, timezone
from src.api.repositories.exam_participants_repository import ExamParticipantsRepository
from src.models.exam_participants import AttendanceStatusEnum
from src.models.exams import ExamStatusEnum

EXAM_NOT_FOUND_MESSAGE = "Exam not found"

class ExamsService:
    @staticmethod
    def list(db: Session, user_id: UUID, limit: int, offset: int):
        """
        Завжди повертає персоналізований список іспитів для користувача.
        """
        repo = ExamsRepository(db)
        attempts_repo = AttemptsRepository(db)
        items_with_status, _ = repo.list(user_id=user_id, limit=limit, offset=offset)
        
        now = datetime.now(timezone.utc)
        open_exams = []
        future_exams = []
        completed_by_user = []

        for exam_model, user_attempts_count in items_with_status:
            exam_schema = Exam.model_validate(exam_model)
            
            # Отримуємо останню спробу для цього іспиту
            last_attempt = attempts_repo.get_last_attempt_for_user_and_exam(user_id, exam_model.id)
            last_attempt_id = str(last_attempt.id) if last_attempt else None
            
            # Додаємо last_attempt_id та user_attempts_count до схеми
            exam_dict = exam_schema.model_dump()
            exam_dict['last_attempt_id'] = last_attempt_id
            exam_dict['user_attempts_count'] = user_attempts_count
            exam_with_attempt = Exam(**exam_dict)

            # Якщо досягнуто max_attempts або є хоча б одна спроба, то іспит у секції "виконані"
            # Перевіряємо, чи є спроби (user_attempts_count > 0) або досягнуто ліміт
            if user_attempts_count > 0 or user_attempts_count >= exam_schema.max_attempts:
                completed_by_user.append(exam_with_attempt)
            # Якщо іспит має статус "open" і ще не завершився, він у секції "відкриті"
            # Перевіряємо статус як з enum (exam_model.status), так і з рядка (exam_schema.status)
            elif (exam_model.status == ExamStatusEnum.open or exam_schema.status == "open") and exam_schema.end_at > now:
                open_exams.append(exam_with_attempt)
            # Інакше, якщо іспит ще не завершився, він у секції "майбутні"
            elif exam_schema.end_at > now:
                future_exams.append(exam_with_attempt)

        return {"open": open_exams, "future": future_exams, "completed": completed_by_user}

    @staticmethod
    def get(db: Session, exam_id: UUID) -> Exam:
        repo = ExamsRepository(db)
        exam = repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)
        return exam
    
    @staticmethod
    def get_for_edit(db: Session, exam_id: UUID) -> ExamWithQuestions:
        """Отримує іспит з питаннями, опціями та matching_data для редагування"""
        repo = ExamsRepository(db)
        exam = repo.get_with_questions(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)
        
        # Форматуємо питання з опціями та matching_data
        # Сортуємо питання за position перед форматуванням
        sorted_questions = sorted(exam.questions, key=lambda q: q.position or 0)
        questions_data = []
        for question in sorted_questions:
            question_dict = {
                "id": question.id,
                "exam_id": question.exam_id,
                "title": question.title,
                "question_type": question.question_type,
                "points": question.points or 1,
                "position": question.position or 0,
                "options": [
                    {
                        "id": opt.id,
                        "question_id": opt.question_id,
                        "text": opt.text,
                        "is_correct": opt.is_correct
                    }
                    for opt in question.options
                ],
                "matching_data": None
            }
            
            # Додаємо matching_data якщо питання типу matching
            if question.question_type.value == "matching" and question.matching_options:
                prompts = []
                matches_map = {}
                for matching_option in question.matching_options:
                    # Генеруємо унікальний temp_id для кожного prompt та match
                    temp_id = str(uuid_lib.uuid4())
                    prompts.append({
                        "temp_id": temp_id,
                        "text": matching_option.prompt,
                        "correct_match_id": temp_id  # Match має той самий ID
                    })
                    matches_map[temp_id] = {
                        "temp_id": temp_id,
                        "text": matching_option.correct_match
                    }
                question_dict["matching_data"] = {
                    "prompts": prompts,
                    "matches": list(matches_map.values())
                }
            
            questions_data.append(question_dict)
        
        # Створюємо ExamWithQuestions з відформатованими питаннями
        exam_dict = {
            "id": exam.id,
            "title": exam.title,
            "instructions": exam.instructions,
            "start_at": exam.start_at,
            "end_at": exam.end_at,
            "duration_minutes": exam.duration_minutes,
            "max_attempts": exam.max_attempts,
            "pass_threshold": exam.pass_threshold,
            "owner_id": exam.owner_id,
            "published": exam.status.value != "draft",
            "status": exam.status.value,  # Додаємо поле status, яке обов'язкове для ExamWithQuestions
            "question_count": len(questions_data),
            "questions": questions_data
        }
        
        return ExamWithQuestions(**exam_dict)

    # --- Question & Option operations for teachers ---
    @staticmethod
    def create_question(db: Session, exam_id: UUID, payload) -> object:
        repo = ExamsRepository(db)
        # verify exam exists
        exam = repo.get(exam_id)
        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)
        return repo.create_question(exam_id, payload)

    @staticmethod
    def update_question(db: Session, question_id: UUID, patch: dict) -> object:
        repo = ExamsRepository(db)
        updated = repo.update_question(question_id, patch)
        if not updated:
            raise NotFoundError("Question not found")
        return updated

    @staticmethod
    def delete_question(db: Session, question_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete_question(question_id)
        if not ok:
            raise NotFoundError("Question not found")

    @staticmethod
    def create_option(db: Session, question_id: UUID, payload) -> object:
        repo = ExamsRepository(db)
        return repo.create_option(question_id, payload)

    @staticmethod
    def update_option(db: Session, option_id: UUID, patch: dict) -> object:
        repo = ExamsRepository(db)
        updated = repo.update_option(option_id, patch)
        if not updated:
            raise NotFoundError("Option not found")
        return updated

    @staticmethod
    def delete_option(db: Session, option_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete_option(option_id)
        if not ok:
            raise NotFoundError("Option not found")

    @staticmethod
    def create(db: Session, payload: ExamCreate, owner_id: UUID) -> Exam:
        repo = ExamsRepository(db)
        # Встановлюємо owner_id з параметра (якщо не встановлено в payload)
        if not payload.owner_id:
            payload.owner_id = owner_id
        exam_model = repo.create(payload)
        # Переконуємося, що статус встановлено як "draft"
        if exam_model.status != ExamStatusEnum.draft:
            exam_model.status = ExamStatusEnum.draft
            db.commit()
            db.refresh(exam_model)
        return exam_model
    
    @staticmethod
    def link_to_course(db: Session, exam_id: UUID, course_id: UUID) -> None:
        """Зв'язує екзамен з курсом"""
        repo = ExamsRepository(db)
        repo.link_to_course(exam_id, course_id)

    @staticmethod
    def update(db: Session, exam_id: UUID, patch: ExamUpdate) -> Exam:
        repo = ExamsRepository(db)
        updated = repo.update(exam_id, patch)
        if not updated:
            raise NotFoundError("Exam not found for update")
        return updated
    
    @staticmethod
    def publish_exam(db: Session, exam_id: UUID) -> Exam:
        """Публікує іспит (змінює статус з draft на published)"""
        repo = ExamsRepository(db)
        updated = repo.publish(exam_id)
        if not updated:
            raise NotFoundError("Exam not found for publish")
        return updated

    @staticmethod
    def delete(db: Session, exam_id: UUID) -> None:
        repo = ExamsRepository(db)
        ok = repo.delete(exam_id)
        if not ok:
            raise NotFoundError("Exam not found for delete")
    
    @staticmethod
    def get_group_statistics(db: Session, course_id: UUID):
        exam_repo = ExamsRepository(db)
        attempt_repo = AttemptsRepository(db)
        course_repo = CoursesRepository(db)

        course = course_repo.get(course_id)
        if not course:
            return []

        exams = exam_repo.get_by_course(course_id)
        
        group_stats = []
        for exam in exams:
            attempts = attempt_repo.get_attempts_by_exam(exam.id)
            total_students = len(attempts)
            
            if total_students == 0:
                continue

            scores = [attempt.earned_points for attempt in attempts if attempt.earned_points is not None]
            if not scores:
                continue
                
            min_score = min(scores)
            max_score = max(scores)
            sorted_scores = sorted(scores)
            median_index = len(sorted_scores) // 2
            median_score = sorted_scores[median_index] if len(sorted_scores) % 2 == 1 else (sorted_scores[median_index - 1] + sorted_scores[median_index]) / 2

            group_stats.append({
                'exam_id': exam.id,
                'exam_name': exam.title,
                'course_id': course_id,
                'course_name': course.name,
                'average_score': sum(scores) / len(scores),
                'min_score': min_score,
                'max_score': max_score,
                'median_score': median_score
            })
        
        return group_stats    

    @staticmethod
    def start_attempt(db: Session, exam_id: UUID, user_id: UUID) -> Attempt:
        exams_repo = ExamsRepository(db)
        exam = exams_repo.get(exam_id)
        attempts_repo = AttemptsRepository(db)

        if not exam:
            raise NotFoundError(EXAM_NOT_FOUND_MESSAGE)

        # Дозвіл лише для учасників іспиту та не "відсутніх"
        participants_repo = ExamParticipantsRepository(db)
        ep = participants_repo.get(exam_id, user_id)
        if not ep or not ep.is_active:
            raise ConflictError("Користувач не зареєстрований як учасник іспиту")

        if ep.attendance_status == AttendanceStatusEnum.absent:
            raise ConflictError("Користувача позначено як відсутнього — доступ до іспиту заборонено")

        # Перевірка ліміту спроб
        user_attempts_count = attempts_repo.get_user_attempt_count(
            user_id=user_id,
            exam_id=exam_id
        )
        if user_attempts_count >= exam.max_attempts:
            raise ConflictError(f"Maximum number of attempts ({exam.max_attempts}) reached for this exam.")

        # Створення спроби
        return attempts_repo.create_attempt(
            exam_id=exam_id,
            user_id=user_id,
            duration_minutes=exam.duration_minutes
        )

    @staticmethod
    def get_exams_for_course(db: Session, course_id: UUID) -> CourseExamsPage:
        course_repo = CoursesRepository(db)
        course = course_repo.get(course_id)
        if not course:
            # було: stats.HTTP_404_NOT_FOUND
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

    @staticmethod
    def get_exam_statistics(db: Session, exam_id: UUID):
        """Отримує статистику по іспиту"""
        attempt_repo = AttemptsRepository(db)
        attempts = attempt_repo.get_attempts_by_exam(exam_id)
        
        if not attempts:
            return {
                'exam_id': exam_id,
                'min_score': None,
                'max_score': None,
                'median_score': None,
                'total_students': 0
            }
        
        scores = [attempt.score_percent for attempt in attempts if attempt.score_percent is not None]
        
        if not scores:
            return {
                'exam_id': exam_id,
                'min_score': None,
                'max_score': None,
                'median_score': None,
                'total_students': len(attempts)
            }
        
        sorted_scores = sorted(scores)
        median_index = len(sorted_scores) // 2
        median_score = sorted_scores[median_index] if len(sorted_scores) % 2 == 1 else (sorted_scores[median_index - 1] + sorted_scores[median_index]) / 2
        
        return {
            'exam_id': exam_id,
            'min_score': min(scores),
            'max_score': max(scores),
            'median_score': median_score,
            'total_students': len(attempts)
        }

    @staticmethod
    def get_exam_progress(db: Session, exam_id: UUID):
        """Отримує динаміку результатів по іспиту (середній бал по датах)"""
        attempt_repo = AttemptsRepository(db)
        attempts = attempt_repo.get_attempts_by_exam(exam_id)
        
        if not attempts:
            return []
        
        # Групуємо спроби за датою завершення
        from collections import defaultdict
        progress_by_date = defaultdict(list)
        
        for attempt in attempts:
            if attempt.earned_points is not None and attempt.submitted_at:
                # Беремо тільки дату без часу для групування
                date_key = attempt.submitted_at.date()
                progress_by_date[date_key].append(attempt.earned_points)
        
        # Формуємо список прогресу
        progress_list = []
        for date, scores in sorted(progress_by_date.items()):
            average_score = sum(scores) / len(scores)
            progress_list.append({
                'exam_id': exam_id,
                'date': datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc),
                'average_score': average_score
            })
        
        return progress_list