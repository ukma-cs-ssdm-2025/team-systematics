from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from typing import Optional, Tuple, List
from src.api.services.journal_service import JournalService
from src.api.repositories.courses_repository import CoursesRepository
from src.api.schemas.courses import CourseCreate, CourseUpdate
from src.models.courses import Course
from src.api.repositories.user_repository import UserRepository
from src.api.errors.app_errors import NotFoundError, ForbiddenError
from src.models.users import User
from src.models.course_supervisors import CourseSupervisor
from src.api.services.exams_service import ExamsService

SUPERVISOR_ONLY = "Доступ дозволений лише наглядачам"
class CoursesService:
    @staticmethod
    def list(
        db: Session,
        current_user_id: UUID,
        limit: int,
        offset: int,
        name_filter: Optional[str] = None,
        teacher_filter: Optional[str] = None,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        min_exams: Optional[int] = None,
        max_exams: Optional[int] = None,
    ) -> Tuple[List[Course], int]:
        return CoursesRepository(db).list(
            current_user_id=current_user_id,
            limit=limit,
            offset=offset,
            name_filter=name_filter,
            teacher_filter=teacher_filter,
            min_students=min_students,
            max_students=max_students,
            min_exams=min_exams,
            max_exams=max_exams,
        )

    @staticmethod
    def get(db: Session, course_id: UUID) -> Optional[Course]:
        return CoursesRepository(db).get(course_id)

    @staticmethod
    def create(db: Session, payload: CourseCreate, owner_id: UUID) -> Course: 
        """
        Створює новий курс після перевірки на унікальність назви та коду.
        """
        repo = CoursesRepository(db)

        # Перевіряємо, чи існує курс з таким кодом або назвою
        existing_course = repo.get_by_code_or_name(code=payload.code, name=payload.name)
        
        if existing_course:
            if existing_course.code.lower() == payload.code.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Курс з кодом '{payload.code}' вже існує."
                )
            if existing_course.name.lower() == payload.name.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Курс з назвою '{payload.name}' вже існує."
                )

        return repo.create(payload, owner_id=owner_id)


    @staticmethod
    def update(db: Session, course_id: UUID, patch: CourseUpdate) -> Optional[Course]:
        return CoursesRepository(db).update(course_id, patch)

    @staticmethod
    def delete(db: Session, course_id: UUID) -> None:
        return CoursesRepository(db).delete(course_id)

    @staticmethod
    def enroll(db: Session, user_id, course_id: UUID) -> None:
        return CoursesRepository(db).enroll(user_id, course_id)

    @staticmethod
    def unenroll(db: Session, user_id, course_id: UUID) -> None:
        """Виписує студента з курсу."""
        return CoursesRepository(db).unenroll(user_id, course_id)

    @staticmethod
    def list_my_courses(
        db: Session,
        user_id,
        limit: int,
        offset: int,
        name_filter: Optional[str] = None,
        min_students: Optional[int] = None,
        max_students: Optional[int] = None,
        min_exams: Optional[int] = None,
        max_exams: Optional[int] = None,
    ):
        return CoursesRepository(db).list_my_courses(
            teacher_id=user_id,
            limit=limit,
            offset=offset,
            name_filter=name_filter,
            min_students=min_students,
            max_students=max_students,
            min_exams=min_exams,
            max_exams=max_exams,
        )

    @staticmethod
    def list_for_supervisor(db: Session, current_user: User, **filters):
        roles = UserRepository(db).get_user_roles(str(current_user.id))
        if "supervisor" not in roles:
            raise ForbiddenError(SUPERVISOR_ONLY)
        return CoursesRepository(db).list_with_stats_for_supervisor(supervisor_id=current_user.id, **filters)

    @staticmethod
    def get_course_details_for_supervisor(db: Session, current_user: User, course_id: UUID):
        roles = UserRepository(db).get_user_roles(str(current_user.id))
        if "supervisor" not in roles:
            raise ForbiddenError(SUPERVISOR_ONLY)

        # Перевіряємо, чи наглядач прив'язаний до цього курсу
        repo = CoursesRepository(db)
        course_supervisor = (
            db.query(CourseSupervisor)
            .filter(
                CourseSupervisor.course_id == course_id,
                CourseSupervisor.supervisor_id == current_user.id
            )
            .first()
        )
        if not course_supervisor:
            raise ForbiddenError("Ви не маєте доступу до цього курсу")

        result = repo.get_course_participants_for_supervisor(course_id)
        if not result:
            raise NotFoundError("Курс не знайдено")
        if not result["students"] and not result["teachers"]:
            return {"message": "Немає зареєстрованих студентів/викладачів"}
        return result
    
    @staticmethod
    def get_course_exam_statistics(db: Session, course_id: UUID):
        exams_service = ExamsService()
        journal_service = JournalService()

        # Отримуємо статистику по іспитах
        group_stats = exams_service.get_group_statistics(db, course_id)
        
        # Отримуємо список студентів та їхніх оцінок
        exam_statistics = journal_service.get_exam_statistics_for_course(db, course_id)

        return {
            "group_stats": group_stats,
            "exam_statistics": exam_statistics
        }

    def get_course_statistics(self, db: Session, user_id: UUID, course_id: UUID):
        # Перевірка ролі викладача
        repo = CoursesRepository(db)
        course = repo.get(course_id)
        if course.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Ви не є викладачем цього курсу")
        
        return self.get_course_exam_statistics(db, course_id)

    @staticmethod
    def get_group_analytics(db: Session, user_id: UUID, course_id: UUID):
        """
        Повертає загальну аналітику оцінок групи для курсу.
        Перевіряє, що запит виконує викладач-власник курсу.
        """
        repo = CoursesRepository(db)
        course = repo.get(course_id)

        if not course:
            raise NotFoundError("Курс не знайдено")

        if course.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ви не є викладачем цього курсу"
            )

        return repo.get_group_score_analytics(course_id)