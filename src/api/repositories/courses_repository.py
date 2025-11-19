from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_, literal, case
from uuid import UUID
from fastapi import Query
from src.api.repositories.exams_repository import ExamsRepository
from src.api.schemas.exams import Exam
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam
from src.models.course_supervisors import CourseSupervisor
from src.api.schemas.courses import CourseCreate, CourseUpdate
from src.models.users import User
from src.models.user_roles import UserRole
from src.models.roles import Role

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
                func.count(func.distinct(CourseEnrollment.user_id)).label("student_count")
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
                case((user_enrollment.user_id.isnot(None), True), else_=False).label("is_enrolled")
            )
        else:
            query = query.add_columns(literal(False).label("is_enrolled"))
            
        return query
    
    @staticmethod
    def _get_teacher_name(owner) -> str:
        """Отримує ім'я викладача з об'єкта owner."""
        if not owner or not owner.first_name or not owner.last_name:
            return ""
        return f"{owner.first_name} {owner.last_name}".strip()
    
    def _get_teachers_list(self, course, owner=None) -> List[str]:
        """Формує список викладачів для курсу."""
        if owner:
            teacher_name = self._get_teacher_name(owner)
        else:
            owner = self.db.query(User).filter(User.id == course.owner_id).first()
            teacher_name = self._get_teacher_name(owner)
        return [teacher_name] if teacher_name else []
    
    def _format_course_results(self, results: List, include_owner: bool = False) -> List[dict]:
        """Форматує результати запиту у список словників для відповіді API."""
        items = []
        for result in results:
            if include_owner and len(result) > 4:
                course, student_count, exam_count, is_enrolled, owner = result
            else:
                course, student_count, exam_count, is_enrolled = result[:4]
                owner = None
            
            teachers = self._get_teachers_list(course, owner)
            
            items.append({
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description,
                "student_count": student_count or 0,
                "exam_count": exam_count or 0,
                "is_enrolled": is_enrolled or False,
                "teachers": teachers
            })
        return items

    @staticmethod
    def _apply_student_exam_filters(
        results: List,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        min_exams: Optional[int] = None,
        max_exams: Optional[int] = None,
    ) -> List:
        """Фільтрує результати за кількістю студентів та іспитів."""
        filtered_results = []
        for result in results:
            _, student_count, exam_count, _ = result[:4]
            student_count = student_count or 0
            exam_count = exam_count or 0
            
            # Фільтр за кількістю студентів
            if min_students is not None and student_count < min_students:
                continue
            if max_students is not None and student_count > max_students:
                continue
            
            # Фільтр за кількістю іспитів
            if min_exams is not None and exam_count < min_exams:
                continue
            if max_exams is not None and exam_count > max_exams:
                continue
            
            filtered_results.append(result)
        return filtered_results

    @staticmethod
    def _apply_name_filter(query, name_filter: Optional[str], owner_alias=None):
        """Застосовує фільтр за назвою/кодом курсу."""
        # owner_alias parameter kept for future use
        if name_filter:
            name_lower = f"%{name_filter.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Course.name).like(name_lower),
                    func.lower(Course.code).like(name_lower)
                )
            )
        return query

    def list(
        self,
        current_user_id: UUID,
        limit: int,
        offset: int,
        name_filter: Optional[str] = None,
        teacher_filter: Optional[str] = None,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        min_exams: Optional[int] = None,
        max_exams: Optional[int] = None,
    ) -> Tuple[List[dict], int]:
        """Повертає загальний список усіх курсів зі статистикою та фільтрами."""
        query = self._build_courses_with_stats_query(current_user_id=current_user_id)
        
        # Додаємо join з викладачем (owner) для фільтрації та отримання даних
        owner_alias = aliased(User)
        query = query.outerjoin(owner_alias, Course.owner_id == owner_alias.id).add_columns(owner_alias)
        
        # Фільтр за назвою/кодом курсу
        query = self._apply_name_filter(query, name_filter, owner_alias)
        
        # Фільтр за викладачем (ПІБ або email)
        if teacher_filter:
            teacher_lower = f"%{teacher_filter.lower()}%"
            teacher_name_expr = func.concat(
                func.coalesce(owner_alias.first_name, ''),
                ' ',
                func.coalesce(owner_alias.last_name, '')
            )
            query = query.filter(
                or_(
                    func.lower(teacher_name_expr).like(teacher_lower),
                    func.lower(owner_alias.email).like(teacher_lower)
                )
            )
        
        # Отримуємо всі результати для фільтрації за кількістю студентів/іспитів
        all_results = query.order_by(Course.name).all()
        
        # Фільтруємо за кількістю студентів та іспитів
        filtered_results = self._apply_student_exam_filters(
            all_results, min_students, max_students, min_exams, max_exams
        )
        
        # Застосовуємо пагінацію
        total = len(filtered_results)
        paginated_results = filtered_results[offset:offset + limit]
        
        items = self._format_course_results(paginated_results, include_owner=True)
        return items, total

    def list_my_courses(
        self,
        teacher_id: UUID,
        limit: int,
        offset: int,
        name_filter: Optional[str] = None,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        min_exams: Optional[int] = None,
        max_exams: Optional[int] = None,
    ) -> Tuple[List[dict], int]:
        """Повертає список курсів для викладача зі статистикою та фільтрами."""
        query = self._build_courses_with_stats_query()
        query = query.filter(Course.owner_id == teacher_id)
        
        # Додаємо join з викладачем (owner) для отримання даних
        owner_alias = aliased(User)
        query = query.outerjoin(owner_alias, Course.owner_id == owner_alias.id).add_columns(owner_alias)
        
        # Фільтр за назвою/кодом курсу
        query = self._apply_name_filter(query, name_filter, owner_alias)
        
        # Отримуємо всі результати для фільтрації за кількістю студентів/іспитів
        all_results = query.order_by(Course.name).all()
        
        # Фільтруємо за кількістю студентів та іспитів
        filtered_results = self._apply_student_exam_filters(
            all_results, min_students, max_students, min_exams, max_exams
        )
        
        # Застосовуємо пагінацію
        total = len(filtered_results)
        paginated_results = filtered_results[offset:offset + limit]
        
        items = self._format_course_results(paginated_results, include_owner=True)
        return items, total

    def get_course_participants_for_supervisor(self, course_id: UUID) -> Optional[dict]:
        """
        Деталі курсу для наглядача:
          - id, name, code, description
          - students: список {id, full_name, email, status}
          - teachers: список {id, full_name, email} (наразі owner як основний викладач)
        Якщо у майбутньому з'явиться таблиця course_teachers — тут треба буде
        замінити логіку формування списку викладачів.
        """
        course = self.get(course_id)
        if not course:
            return None

        # Студенти (enrolled) - тільки користувачі з роллю 'student'
        stu_rows = (
            self.db.query(User.id, User.first_name, User.last_name, User.patronymic, User.email)
            .join(CourseEnrollment, CourseEnrollment.user_id == User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(
                CourseEnrollment.course_id == course_id,
                Role.name == 'student'
            )
            .order_by(User.last_name, User.first_name)
            .all()
        )
        students = [
            {
                "id": str(row.id),
                "full_name": f"{row.last_name} {row.first_name} {row.patronymic or ''}".strip(),
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
                    "id": str(owner_row.id),
                    "full_name": f"{owner_row.first_name} {owner_row.last_name}".strip(),
                    "email": owner_row.email,
                }
            )

        return {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description,
            "students": students,
            "teachers": teachers
        }


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

    def unenroll(self, user_id, course_id: UUID) -> None:
        """Виписує студента з курсу."""
        enrollment = (
            self.db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id)
            .first()
        )
        if enrollment:
            self.db.delete(enrollment)
        self.db.commit()

    def get_student_count(self, course_id: UUID) -> int:
        """Підраховує кількість унікальних студентів, записаних на курс."""
        return self.db.query(func.count(func.distinct(CourseEnrollment.user_id))).filter(CourseEnrollment.course_id == course_id).scalar() or 0
    
    def get_course_statistics(self, course_id: UUID) -> dict:
        """Метод для отримання статистики по курсу."""
        # Використовуємо ExamsRepository, щоб отримати статистику по кожному іспиту
        exams = self.db.query(Exam).filter(Exam.course_id == course_id).all()
        repo = ExamsRepository(self.db)
    
        stats = {}  # Змінено на dict замість списку
        for exam in exams:
            exam_stats = repo.get_exam_statistics(exam.id)
            stats[exam.id] = {  # Ключем буде exam_id
                "exam_title": exam.title,
                "average_score": exam_stats.get("average_score"),
                "min_score": exam_stats.get("min_score"),
                "max_score": exam_stats.get("max_score"),
                "median_score": exam_stats.get("median_score"),
            }

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
        ).order_by(Attempt.user_id, Attempt.earned_points.desc(), Attempt.submitted_at.desc()).all()

        if not attempts:
            return {
                "total_students": total_students,
                "students_completed": 0,
                "total_attempts": 0,
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "median_score": None,
                "scores": []
            }

        # Для гістограми використовуємо найкращу спробу кожного студента
        # (якщо студент зробив кілька спроб, беремо ту, де найвищий бал)
        best_attempts_by_student = {}
        for attempt in attempts:
            user_id = attempt.user_id
            if user_id not in best_attempts_by_student:
                best_attempts_by_student[user_id] = attempt
            elif attempt.earned_points > best_attempts_by_student[user_id].earned_points:
                best_attempts_by_student[user_id] = attempt

        # Список балів для гістограми (тільки найкращі спроби)
        scores = [a.earned_points for a in best_attempts_by_student.values()]
        unique_completed_students = len(best_attempts_by_student)
        total_attempts = len(attempts)

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
            "total_attempts": total_attempts,
            "average_score": round(avg, 2) if avg is not None else None,
            "min_score": round(mn, 2) if mn is not None else None,
            "max_score": round(mx, 2) if mx is not None else None,
            "median_score": round(median, 2) if median is not None else None,
            "scores": scores
        }

    def list_with_stats_for_supervisor(
        self,
        supervisor_id: UUID,
        title_filter: Optional[str] = None,
        teacher_filter: Optional[str] = None,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """
        Повертає список курсів для наглядача з фільтрами.
        Показує тільки курси, до яких прив'язаний даний наглядач.
        Формат: {id, name, code, students_count, teachers: [full_name, ...]}
        """
        # Підрахунок унікальних студентів
        student_count_subquery = (
            self.db.query(
                CourseEnrollment.course_id,
                func.count(func.distinct(CourseEnrollment.user_id)).label("students_count")
            )
            .group_by(CourseEnrollment.course_id)
            .subquery()
        )
        
        # Отримуємо викладачів (owner) для кожного курсу
        owner_alias = aliased(User)
        # Використовуємо coalesce для обробки NULL значень та конкатенацію
        teacher_name_expr = func.concat(
            func.coalesce(owner_alias.first_name, ''),
            ' ',
            func.coalesce(owner_alias.last_name, '')
        )
        
        query = (
            self.db.query(
                Course.id,
                Course.name,
                Course.code,
                func.coalesce(student_count_subquery.c.students_count, 0).label("students_count"),
                teacher_name_expr.label("teacher_name"),
                owner_alias.email.label("teacher_email")
            )
            .join(CourseSupervisor, CourseSupervisor.course_id == Course.id)
            .filter(CourseSupervisor.supervisor_id == supervisor_id)
            .outerjoin(student_count_subquery, Course.id == student_count_subquery.c.course_id)
            .outerjoin(owner_alias, Course.owner_id == owner_alias.id)
        )
        
        # Фільтр за назвою/кодом курсу
        if title_filter:
            title_lower = f"%{title_filter.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Course.name).like(title_lower),
                    func.lower(Course.code).like(title_lower)
                )
            )
        
        # Фільтр за викладачем (ПІБ або email)
        if teacher_filter:
            teacher_lower = f"%{teacher_filter.lower()}%"
            query = query.filter(
                or_(
                    func.lower(teacher_name_expr).like(teacher_lower),
                    func.lower(owner_alias.email).like(teacher_lower)
                )
            )
        
        # Отримуємо всі результати для групування
        all_results = query.all()
        
        # Групуємо за курсом та збираємо викладачів
        courses_dict = {}
        for course_id, name, code, students_count, teacher_name, _teacher_email in all_results:
            if course_id not in courses_dict:
                courses_dict[course_id] = {
                    "id": course_id,
                    "name": name,
                    "code": code,
                    "students_count": students_count or 0,
                    "teachers": []
                }
            if teacher_name and teacher_name.strip():
                # Додаємо тільки унікальні імена викладачів
                if teacher_name.strip() not in courses_dict[course_id]["teachers"]:
                    courses_dict[course_id]["teachers"].append(teacher_name.strip())
        
        # Фільтр за кількістю студентів (після групування)
        if min_students is not None:
            courses_dict = {k: v for k, v in courses_dict.items() if v["students_count"] >= min_students}
        if max_students is not None:
            courses_dict = {k: v for k, v in courses_dict.items() if v["students_count"] <= max_students}
        
        # Конвертуємо в список та сортуємо
        items = list(courses_dict.values())
        items.sort(key=lambda x: x["name"])
        
        # Застосовуємо пагінацію
        total = len(items)
        paginated_items = items[offset:offset + limit]
        
        return paginated_items, total
    