from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_, literal
from uuid import UUID
from fastapi import Query
from api.schemas.exams import Exam
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam
from src.api.schemas.courses import CourseCreate, CourseUpdate
from src.models.users import User

class CoursesRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_code_or_name(self, code: str, name: str) -> Optional[Course]:
        """
        Знаходить курс за кодом або назвою, ігноруючи регістр.
        Використовується для перевірки на унікальність.
        """
        return self.db.query(Course).filter(
            or_(
                func.lower(Course.code) == func.lower(code),
                func.lower(Course.name) == func.lower(name)
            )
        ).first()


    def _build_courses_with_stats_query(self, current_user_id: Optional[UUID] = None) -> Query:
        """
        Створює базовий запит для отримання курсів зі статистикою.
        Якщо передано current_user_id, додає поле is_enrolled.
        """
        student_count_subquery = (
            self.db.query(
                CourseEnrollment.course_id,
                func.count(CourseEnrollment.user_id).label("student_count")
            ).group_by(CourseEnrollment.course_id).subquery()
        )
        
        exam_count_subquery = (
            self.db.query(
                CourseExam.course_id,
                func.count(CourseExam.exam_id).label("exam_count")
            ).group_by(CourseExam.course_id).subquery()
        )

        query = self.db.query(
            Course,
            student_count_subquery.c.student_count,
            exam_count_subquery.c.exam_count
        ).outerjoin(
            student_count_subquery, Course.id == student_count_subquery.c.course_id
        ).outerjoin(
            exam_count_subquery, Course.id == exam_count_subquery.c.course_id
        )

        # Перевіряємо, чи записаний вже студент на обраний курс
        if current_user_id:
            user_enrollment = aliased(CourseEnrollment)
            query = query.outerjoin(
                user_enrollment,
                (user_enrollment.course_id == Course.id) & (user_enrollment.user_id == current_user_id)
            ).add_columns(
                (user_enrollment.user_id != None).label("is_enrolled")
            )
        else:
            query = query.add_columns(literal(False).label("is_enrolled"))
            
        return query
    
    def _format_course_results(self, results: List) -> List[dict]:
        """Форматує результати запиту у список словників для відповіді API."""
        items = []
        for course, student_count, exam_count, is_enrolled in results:
            items.append({
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description,
                "student_count": student_count or 0,
                "exam_count": exam_count or 0,
                "is_enrolled": is_enrolled or False
            })
        return items

    def list(self, current_user_id: UUID, limit: int, offset: int) -> Tuple[List[dict], int]:
        """Повертає загальний список усіх курсів зі статистикою."""
        query = self._build_courses_with_stats_query(current_user_id=current_user_id)
        total = query.count()
        results = query.order_by(Course.name).limit(limit).offset(offset).all()
        items = self._format_course_results(results)
        return items, total

    def list_my_courses(self, teacher_id: UUID, limit: int, offset: int) -> Tuple[List[dict], int]:
        """Повертає список курсів для викладача зі статистикою."""
        query = self._build_courses_with_stats_query()
        query = query.filter(Course.owner_id == teacher_id)
        total = query.count()
        results = query.order_by(Course.name).limit(limit).offset(offset).all()
        items = self._format_course_results(results)
        return items, total

    def get_course_participants_for_supervisor(self, course_id: UUID) -> dict:
        """
        Деталі курсу для наглядача:
          - students: список {id, full_name, email}
          - teachers: список {id, full_name, email} (наразі owner як основний викладач)
        Якщо у майбутньому з'явиться таблиця course_teachers — тут треба буде
        замінити логіку формування списку викладачів.
        """
        course = self.get(course_id)
        if not course:
            return {"students": [], "teachers": []}

        # Студенти (enrolled)
        stu_rows = (
            self.db.query(User.id, User.first_name, User.last_name, User.email)
            .join(CourseEnrollment, CourseEnrollment.user_id == User.id)
            .filter(CourseEnrollment.course_id == course_id)
            .order_by(User.last_name, User.first_name)
            .all()
        )
        students = [
            {
                "id": row.id,
                "full_name": f"{row.first_name} {row.last_name}".strip(),
                "email": row.email,
                "status": "enrolled",
            }
            for row in stu_rows
        ]

        # Викладачі (owner як мінімум один)
        owner_row = (
            self.db.query(User.id, User.first_name, User.last_name, User.email)
            .filter(User.id == course.owner_id)
            .first()
        )
        teachers: List[dict] = []
        if owner_row:
            teachers.append(
                {
                    "id": owner_row.id,
                    "full_name": f"{owner_row.first_name} {owner_row.last_name}".strip(),
                    "email": owner_row.email,
                }
            )

        return {"students": students, "teachers": teachers}


    def get(self, course_id: UUID) -> Optional[Course]:
        return self.db.query(Course).filter(Course.id == course_id).first()

    def create(self, payload: CourseCreate, owner_id: UUID) -> Course:
        course_data = payload.model_dump()
        course_data['owner_id'] = owner_id
        
        entity = Course(**course_data)
        
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, course_id: UUID, patch: CourseUpdate) -> Optional[Course]:
        entity = self.get(course_id)
        if not entity:
            return None
        data = {k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None}
        for k, v in data.items():
            setattr(entity, k, v)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, course_id: UUID) -> None:
        entity = self.get(course_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()

    def enroll(self, user_id, course_id: UUID) -> None:
        exists = (
            self.db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id)
            .first()
        )
        if exists:
            return
        self.db.add(CourseEnrollment(user_id=user_id, course_id=course_id))
        self.db.commit()

    def get_student_count(self, course_id: UUID) -> int:
        """Підраховує кількість студентів, записаних на курс."""
        return self.db.query(func.count(CourseEnrollment.user_id)).filter(CourseEnrollment.course_id == course_id).scalar() or 0
    
    def get_course_statistics(self, course_id: UUID) -> dict:
        """Метод для отримання статистики по курсу"""
        # Використовуємо ExamsRepository, щоб отримати статистику по кожному іспиту
        from src.api.repositories.exams_repository import ExamsRepository

        exams = self.db.query(Exam).filter(Exam.course_id == course_id).all()
        repo = ExamsRepository(self.db)

        stats = []
        for exam in exams:
            exam_stats = repo.get_exam_statistics(exam.id)
            stats.append({
                "exam_id": exam.id,
                "exam_title": exam.title,
                "average_score": exam_stats.get("average_score"),
                "min_score": exam_stats.get("min_score"),
                "max_score": exam_stats.get("max_score"),
                "median_score": exam_stats.get("median_score"),
            })
        return stats
    
    def get_group_score_analytics(self, course_id: UUID) -> dict:
        """
        Отримує аналітику оцінок групи студентів для курсу.
        Повертає словник із загальною статистикою по усіх завершених спробах
        студентів, що записані на курс (average, min, max, median), а також
        список оцінок для подальшої візуалізації.
        """
        from src.models.attempts import Attempt, AttemptStatus
        # збираємо id студентів, записаних на курс
        student_rows = self.db.query(CourseEnrollment.user_id).filter(
            CourseEnrollment.course_id == course_id
        ).all()
        student_ids = [r[0] for r in student_rows]
        total_students = len(student_ids)

        if total_students == 0:
            return {
                "total_students": 0,
                "students_completed": 0,
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "median_score": None,
                "scores": []
            }

        # список іспитів, пов'язаних з курсом
        exam_rows = self.db.query(CourseExam.exam_id).filter(CourseExam.course_id == course_id).all()
        exam_ids = [r[0] for r in exam_rows]

        if not exam_ids:
            return {
                "total_students": total_students,
                "students_completed": 0,
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "median_score": None,
                "scores": []
            }

        # отримуємо завершені і оцінені спроби студентів по цим іспитам
        attempts = self.db.query(Attempt).filter(
            Attempt.user_id.in_(student_ids),
            Attempt.exam_id.in_(exam_ids),
            Attempt.status == AttemptStatus.completed,
            Attempt.earned_points.isnot(None)
        ).all()

        if not attempts:
            return {
                "total_students": total_students,
                "students_completed": 0,
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "median_score": None,
                "scores": []
            }

        scores = [a.earned_points for a in attempts]
        unique_completed_students = len(set(a.user_id for a in attempts))

        avg = sum(scores) / len(scores) if scores else None
        mn = min(scores) if scores else None
        mx = max(scores) if scores else None
        sorted_scores = sorted(scores)
        if not sorted_scores:
            median = None
        elif len(sorted_scores) % 2 == 0:
            mid = len(sorted_scores) // 2
            median = (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
        else:
            median = sorted_scores[len(sorted_scores) // 2]

        return {
            "total_students": total_students,
            "students_completed": unique_completed_students,
            "average_score": round(avg, 2) if avg is not None else None,
            "min_score": round(mn, 2) if mn is not None else None,
            "max_score": round(mx, 2) if mx is not None else None,
            "median_score": round(median, 2) if median is not None else None,
            "scores": scores
        }
    