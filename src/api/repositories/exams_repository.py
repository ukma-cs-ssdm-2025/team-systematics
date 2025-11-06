from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
from uuid import UUID
from typing import List, Tuple, Optional
from src.models.exams import Exam
from src.models.exams import Question, Option
from src.models.attempts import Attempt, AttemptStatus
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam
from src.api.schemas.exams import ExamCreate, ExamUpdate

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
            CourseEnrollment.user_id == user_id
        ).outerjoin(
            attempt_count_subquery, Exam.id == attempt_count_subquery.c.exam_id
        )

        total = query.count()
        items = query.order_by(Exam.end_at.desc()).limit(limit).offset(offset).all()
        
        return items, total

    # ВИПРАВЛЕНО: Замінено 'Exam | None' на 'Optional[Exam]'
    def get(self, exam_id: UUID) -> Optional[Exam]:
        return self.db.query(Exam).filter(Exam.id == exam_id).first()

    def create(self, payload: ExamCreate) -> Exam:
        new_exam = Exam(**payload.model_dump())
        self.db.add(new_exam)
        self.db.commit()
        self.db.refresh(new_exam)
        return new_exam

    # --- Question & Option management ---
    def create_question(self, exam_id: UUID, payload) -> Question:
        q = Question(**{k: v for k, v in payload.items() if k != 'options'})
        q.exam_id = exam_id
        self.db.add(q)
        # ensure q.id is populated before creating options
        self.db.flush()
        # add options if provided
        options = payload.get('options') or []
        for opt in options:
            o = Option(question_id=q.id, text=opt.get('text'), is_correct=opt.get('is_correct', False))
            self.db.add(o)

        self.db.commit()
        # refresh q and return
        self.db.refresh(q)
        return q

    def update_question(self, question_id: UUID, patch: dict) -> Optional[Question]:
        q = self.db.query(Question).filter(Question.id == question_id).first()
        if not q:
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
        exam = self.get(exam_id)
        if not exam:
            return None
        
        patch_data = patch.model_dump(exclude_unset=True)
        for key, value in patch_data.items():
            setattr(exam, key, value)
            
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def delete(self, exam_id: UUID) -> bool:
        exam = self.get(exam_id)
        if not exam:
            return False
        
        self.db.delete(exam)
        self.db.commit()
        return True

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