from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
from uuid import UUID
from typing import List, Tuple, Optional
import logging
from src.api.services.statistics_service import StatisticsService
from src.models.exams import Exam, ExamStatusEnum
from src.models.exams import Question, Option
from src.models.attempts import Attempt, AttemptStatus
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam
from src.models.matching_options import MatchingOption
from src.api.schemas.exams import ExamCreate, ExamUpdate

logger = logging.getLogger(__name__)

class ExamsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, user_id: UUID, limit: int, offset: int) -> Tuple[List[Tuple[Exam, int]], int]:
        """
        Повертає персоналізований список іспитів для конкретного користувача
        на основі курсів, на які він записаний
        """
        attempt_count_subquery = self.db.query(
            Attempt.exam_id,
            func.count(Attempt.id).label("user_attempts_count")
        ).filter(
            Attempt.user_id == user_id
        ).group_by(Attempt.exam_id).subquery()

        query = self.db.query(
            Exam,
            func.coalesce(attempt_count_subquery.c.user_attempts_count, 0).label("user_attempts_count")
        ).join(
            CourseExam, CourseExam.exam_id == Exam.id
        ).join(
            Course, Course.id == CourseExam.course_id
        ).join(
            CourseEnrollment, CourseEnrollment.course_id == Course.id
        ).filter(
            CourseEnrollment.user_id == user_id,
            Exam.status != ExamStatusEnum.draft  # Виключаємо чернетки зі списку для студентів
        ).outerjoin(
            attempt_count_subquery, Exam.id == attempt_count_subquery.c.exam_id
        )

        total = query.count()
        items = query.order_by(Exam.end_at.desc()).limit(limit).offset(offset).all()
        
        return items, total

    # ВИПРАВЛЕНО: Замінено 'Exam | None' на 'Optional[Exam]'
    def get(self, exam_id: UUID) -> Optional[Exam]:
        if not exam_id:
            logger.warning("get() called with None or empty exam_id")
            return None
        exam = self.db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            logger.debug(f"Exam with id {exam_id} not found")
        return exam
    
    def get_with_questions(self, exam_id: UUID) -> Optional[Exam]:
        """Отримує іспит разом з питаннями, опціями та matching_data"""
        from sqlalchemy.orm import selectinload
        exam = self.db.query(Exam).options(
            selectinload(Exam.questions).selectinload(Question.options),
            selectinload(Exam.questions).selectinload(Question.matching_options)
        ).filter(Exam.id == exam_id).first()
        
        # Сортуємо питання за position після завантаження та видаляємо дублікати
        if exam and exam.questions:
            # Видаляємо дублікати за id (на випадок, якщо вони з'явилися)
            seen_ids = set()
            unique_questions = []
            for q in exam.questions:
                if q.id not in seen_ids:
                    seen_ids.add(q.id)
                    unique_questions.append(q)
            exam.questions = unique_questions
            # Сортуємо за position
            exam.questions.sort(key=lambda q: q.position or 0)
        
        return exam

    def create(self, payload: ExamCreate) -> Exam:
        exam_data = payload.model_dump()
        # Виключаємо status з exam_data, якщо він там є (не повинен бути)
        exam_data.pop('status', None)
        # Створюємо об'єкт іспиту
        new_exam = Exam(**exam_data)
        # Явно встановлюємо статус як "draft" при створенні іспиту
        # (встановлюємо після створення об'єкта, щоб гарантувати правильне значення)
        new_exam.status = ExamStatusEnum.draft
        logger.debug(f"Creating exam with status: {new_exam.status}, status value: {new_exam.status.value}")
        self.db.add(new_exam)
        self.db.commit()
        self.db.refresh(new_exam)
        logger.debug(f"Exam created with status: {new_exam.status}, status value: {new_exam.status.value}")
        return new_exam
    
    def link_to_course(self, exam_id: UUID, course_id: UUID) -> None:
        """Зв'язує екзамен з курсом через таблицю course_exams"""
        # Перевіряємо, чи зв'язок вже існує
        existing = self.db.query(CourseExam).filter(
            CourseExam.exam_id == exam_id,
            CourseExam.course_id == course_id
        ).first()
        if existing:
            return  # Зв'язок вже існує
        
        course_exam = CourseExam(exam_id=exam_id, course_id=course_id)
        self.db.add(course_exam)
        self.db.commit()

    # --- Question & Option management ---
    def create_question(self, exam_id: UUID, payload) -> Question:
        # validate and prepare
        self._validate_question_payload(exam_id, payload)
        question_data = {k: v for k, v in payload.items() if k not in ('options', 'matching_data')}

        # create question and ensure id is available
        q = Question(**question_data)
        q.exam_id = exam_id
        self.db.add(q)
        self.db.flush()

        # add options and matching data
        options = payload.get('options') or []
        self._add_options(q.id, options)

        matching_data = payload.get('matching_data')
        if matching_data:
            self._add_matching_options(q.id, matching_data)

        self.db.commit()
        self.db.refresh(q)
        return q

    @staticmethod
    def _validate_question_payload(exam_id: UUID, payload) -> None:
        if not payload:
            raise ValueError("Payload cannot be None or empty")
        if not isinstance(payload, dict):
            raise TypeError(f"Payload must be a dict, got {type(payload).__name__}")
        if not exam_id:
            raise ValueError("exam_id cannot be None or empty")
        if not payload.get('title'):
            raise ValueError("Question title is required")
        if 'question_type' not in payload:
            raise ValueError("Question type is required")

    def _add_options(self, question_id: UUID, options) -> None:
        if not options:
            return
        if not isinstance(options, list):
            raise TypeError(f"Options must be a list, got {type(options).__name__}")
        for opt in options:
            if not isinstance(opt, dict):
                raise TypeError(f"Each option must be a dict, got {type(opt).__name__}")
            o = Option(question_id=question_id, text=opt.get('text'), is_correct=opt.get('is_correct', False))
            self.db.add(o)

    def _add_matching_options(self, question_id: UUID, matching_data) -> None:
        if not isinstance(matching_data, dict):
            raise TypeError(f"Matching data must be a dict, got {type(matching_data).__name__}")
        prompts = matching_data.get('prompts', [])
        if not isinstance(prompts, list):
            raise TypeError(f"Prompts must be a list, got {type(prompts).__name__}")
        for prompt_data in prompts:
            if not isinstance(prompt_data, dict):
                raise TypeError(f"Each prompt must be a dict, got {type(prompt_data).__name__}")
            matching_option = MatchingOption(
                question_id=question_id,
                prompt=prompt_data.get('text', ''),
                correct_match=prompt_data.get('correct_match', ''),
            )
            self.db.add(matching_option)

    def update_question(self, question_id: UUID, patch: dict) -> Optional[Question]:
        if not question_id:
            logger.warning("update_question() called with None or empty question_id")
            return None
        if not patch:
            logger.warning("update_question() called with None or empty patch")
            return None
        q = self.db.query(Question).filter(Question.id == question_id).first()
        if not q:
            logger.debug(f"Question with id {question_id} not found for update")
            return None
        for k, v in patch.items():
            if k == 'options':
                # options should be managed via option endpoints
                continue
            setattr(q, k, v)
        self.db.commit()
        self.db.refresh(q)
        return q

    def delete_question(self, question_id: UUID) -> bool:
        q = self.db.query(Question).filter(Question.id == question_id).first()
        if not q:
            return False
        self.db.delete(q)
        self.db.commit()
        return True

    def create_option(self, question_id: UUID, payload) -> Option:
        o = Option(question_id=question_id, text=payload.get('text'), is_correct=payload.get('is_correct', False))
        self.db.add(o)
        self.db.commit()
        self.db.refresh(o)
        return o

    def update_option(self, option_id: UUID, patch: dict) -> Optional[Option]:
        o = self.db.query(Option).filter(Option.id == option_id).first()
        if not o:
            return None
        for k, v in patch.items():
            setattr(o, k, v)
        self.db.commit()
        self.db.refresh(o)
        return o

    def delete_option(self, option_id: UUID) -> bool:
        o = self.db.query(Option).filter(Option.id == option_id).first()
        if not o:
            return False
        self.db.delete(o)
        self.db.commit()
        return True

    # ВИПРАВЛЕНО: Замінено 'Exam | None' на 'Optional[Exam]'
    def update(self, exam_id: UUID, patch: ExamUpdate) -> Optional[Exam]:
        if not exam_id:
            logger.warning("update() called with None or empty exam_id")
            return None
        exam = self.get(exam_id)
        if not exam:
            logger.debug(f"Exam with id {exam_id} not found for update")
            return None
        
        patch_data = patch.model_dump(exclude_unset=True)
        # Виключаємо поля, які не повинні оновлюватися через цей метод
        excluded_fields = {'exam_id', 'owner_id', 'id'}  # Ці поля не повинні оновлюватися
        for key, value in patch_data.items():
            if key not in excluded_fields:
                # Конвертуємо published в status, якщо потрібно
                if key == 'published':
                    from src.models.exams import ExamStatusEnum
                    exam.status = ExamStatusEnum.published if value else ExamStatusEnum.draft
                else:
                    setattr(exam, key, value)
            
        self.db.commit()
        self.db.refresh(exam)
        return exam
    
    def publish(self, exam_id: UUID) -> Optional[Exam]:
        """Змінює статус іспиту з draft на published"""
        exam = self.get(exam_id)
        if not exam:
            return None
        exam.status = ExamStatusEnum.published
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def delete(self, exam_id: UUID) -> bool:
        exam = self.get(exam_id)
        if not exam:
            return False
        
        # Видаляємо в правильному порядку, щоб уникнути проблем з foreign key:
        # 1. Спочатку видаляємо plagiarism_checks (вони посилаються на attempts)
        # 2. Потім видаляємо attempts (вони посилаються на exams)
        # 3. Нарешті видаляємо exam
        from src.models.attempts import Attempt, PlagiarismCheck
        
        # Отримуємо всі attempt_id для цього іспиту
        attempt_ids = [attempt.id for attempt in self.db.query(Attempt.id).filter(Attempt.exam_id == exam_id).all()]
        
        # Видаляємо plagiarism_checks для цих attempts
        if attempt_ids:
            self.db.query(PlagiarismCheck).filter(PlagiarismCheck.attempt_id.in_(attempt_ids)).delete()
        
        # Видаляємо attempts
        self.db.query(Attempt).filter(Attempt.exam_id == exam_id).delete()
        
        # Видаляємо exam
        self.db.delete(exam)
        self.db.commit()
        return True

    def get_by_course(self, course_id: UUID) -> List[Exam]:
        """Отримує список іспитів для курсу"""
        return (
            self.db.query(Exam)
            .join(CourseExam, Exam.id == CourseExam.exam_id)
            .filter(CourseExam.course_id == course_id)
            .all()
        )

    def get_exams_stats_for_course(self, course_id: UUID) -> List[Tuple]:
        """
        Отримує список іспитів для курсу разом з розрахованою статистикою:
        - Кількість питань
        - Кількість завершених спроб
        - Середній бал
        - Кількість робіт, що очікують на перевірку
        """
        # Підзапит для підрахунку питань
        questions_count_sq = (
            self.db.query(
                Question.exam_id,
                func.count(Question.id).label("questions_count")
            )
            .group_by(Question.exam_id)
            .subquery()
        )

        # Підзапит для статистики по спробах (attempts)
        attempt_stats_sq = (
            self.db.query(
                Attempt.exam_id,
                func.count(case((Attempt.earned_points != None, Attempt.id))).label("students_completed"),
                func.avg(Attempt.earned_points).label("average_grade"),
                func.count(case((Attempt.status == AttemptStatus.submitted, Attempt.id))).label("pending_reviews")
            )
            .group_by(Attempt.exam_id)
            .subquery()
        )

        # Основний запит
        results = (
            self.db.query(
                Exam,
                questions_count_sq.c.questions_count,
                attempt_stats_sq.c.students_completed,
                attempt_stats_sq.c.average_grade,
                attempt_stats_sq.c.pending_reviews
            )
            .join(Exam.courses)
            .filter(Course.id == course_id)
            .outerjoin(questions_count_sq, Exam.id == questions_count_sq.c.exam_id)
            .outerjoin(attempt_stats_sq, Exam.id == attempt_stats_sq.c.exam_id)
            .order_by(Exam.start_at.desc())
            .all()
        )
        return results

    def get_exam_statistics(self, exam_id: UUID) -> dict:
        """Метод для отримання статистики по іспиту"""
        attempts = self.db.query(Attempt).filter(Attempt.exam_id == exam_id).all()
        
        scores = [attempt.earned_points for attempt in attempts if attempt.earned_points is not None]
        
        return StatisticsService.calculate_statistics(scores)