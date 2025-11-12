from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from typing import Optional, Tuple, List
from src.api.repositories.courses_repository import CoursesRepository
from src.api.schemas.courses import CourseCreate, CourseUpdate
from src.models.courses import Course
from src.api.repositories.user_repository import UserRepository
from src.api.errors.app_errors import NotFoundError, ForbiddenError
from src.models.users import User

SUPERVISOR_ONLY = "Доступ дозволений лише наглядачам"
class CoursesService:
    def list(
        self,
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

    def get(self, db: Session, course_id: UUID) -> Optional[Course]:
        return CoursesRepository(db).get(course_id)

    def create(self, db: Session, payload: CourseCreate, owner_id: UUID) -> Course: 
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


    def update(self, db: Session, course_id: UUID, patch: CourseUpdate) -> Optional[Course]:
        return CoursesRepository(db).update(course_id, patch)

    def delete(self, db: Session, course_id: UUID) -> None:
        return CoursesRepository(db).delete(course_id)

    def enroll(self, db: Session, user_id, course_id: UUID) -> None:
        return CoursesRepository(db).enroll(user_id, course_id)

    def list_my_courses(
        self,
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

    def list_for_supervisor(self, db: Session, current_user: User, **filters):
        roles = UserRepository(db).get_user_roles(str(current_user.id))
        if "supervisor" not in roles:
            raise ForbiddenError(SUPERVISOR_ONLY)
        return CoursesRepository(db).list_with_stats_for_supervisor(**filters)

    def get_course_details_for_supervisor(self, db: Session, current_user: User, course_id: UUID):
        roles = UserRepository(db).get_user_roles(str(current_user.id))
        if "supervisor" not in roles:
            raise ForbiddenError(SUPERVISOR_ONLY)

        result = CoursesRepository(db).get_course_participants_for_supervisor(course_id)
        if not result:
            raise NotFoundError("Курс не знайдено")
        if not result["students"] and not result["teachers"]:
            return {"message": "Немає зареєстрованих студентів/викладачів"}
        return result

