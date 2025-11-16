from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.analytics import CourseAnalyticsResponse, GroupScoreAnalytics
from src.models.users import User
from src.api.schemas.exams import CourseExamsPage
from src.api.schemas.courses import (
    Course,
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CoursesPage,
    CourseSupervisorListItem,
    CourseSupervisorDetails,
)
from src.api.services.courses_service import CoursesService
from src.api.services.exams_service import ExamsService
from src.api.database import get_db
from src.utils.auth import get_current_user_with_role, require_role
from .versioning import require_api_version

TEACHER_ONLY_ACCESS = "Цей функціонал доступний лише для викладачів"
FILTER_NAME_DESCRIPTION = "Фільтр за назвою/кодом курсу"
MIN_STUDENTS_DESCRIPTION = "Мін. к-сть студентів"
MAX_STUDENTS_DESCRIPTION = "Макс. к-сть студентів"


class CoursesController:
    def __init__(self, service: CoursesService) -> None:
        self.service = service
        self.exams_service = ExamsService()
        self.router = APIRouter(
            prefix="/courses",
            tags=["Courses"],
            dependencies=[Depends(require_api_version)],
        )

        # реєстрація маршрутів
        self.router.get(
            "/me",
            response_model=CoursesPage,
            summary="Список моїх курсів (лише для викладача)",
        )(self.list_my_courses)

        self.router.get(
            "",
            response_model=CoursesPage,
            summary="Список усіх курсів (для студентів)",
        )(self.list_courses)

        # /supervisor — перед /{course_id}, щоб не конфліктувати з UUID
        self.router.get(
            "/supervisor",
            response_model=list[CourseSupervisorListItem],
            summary="Список курсів для наглядача",
        )(self.list_courses_for_supervisor)

        self.router.get(
            "/supervisor/{course_id}",
            response_model=CourseSupervisorDetails,
            summary="Деталі курсу для наглядача",
        )(self.get_course_details_for_supervisor)

        self.router.get(
            "/{course_id}/analytics",
            response_model=CourseAnalyticsResponse,
            summary="Аналітика курсу: статистика по іспитах",
        )(self.get_course_analytics)

        self.router.get(
            "/{course_id}/group-analytics",
            response_model=GroupScoreAnalytics,
            summary="Аналітика групи: середній/мін/макс/медіана оцінок",
        )(self.get_group_analytics)

        self.router.post(
            "",
            response_model=CourseBase,
            status_code=status.HTTP_201_CREATED,
            summary="Створити новий курс (лише для викладача)",
        )(self.create_course)

        self.router.get(
            "/{course_id}",
            response_model=Course,
        )(self.get_course)

        self.router.patch(
            "/{course_id}",
            response_model=Course,
        )(self.update_course)

        self.router.delete(
            "/{course_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_course)

        self.router.post(
            "/{course_id}/enroll",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.enroll)

        self.router.delete(
            "/{course_id}/enroll",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.unenroll)

        self.router.get(
            "/{course_id}/exams",
            response_model=CourseExamsPage,
            summary="Список іспитів для курсу (для викладача та наглядача)",
        )(self.list_course_exams)

    # ---- допоміжні методи ----

    @staticmethod
    def _ensure_role(
        current_user: User,
        allowed_roles: set[str],
        detail: str,
    ) -> None:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

    # ---- ендпоінти ----

    def list_my_courses(
        self,
        name: Optional[str] = Query(None, description=FILTER_NAME_DESCRIPTION),
        min_students: Optional[int] = Query(
            None, ge=0, description=MIN_STUDENTS_DESCRIPTION
        ),
        max_students: Optional[int] = Query(
            None, ge=0, description=MAX_STUDENTS_DESCRIPTION
        ),
        min_exams: Optional[int] = Query(None, ge=0, description="Мін. к-сть іспитів"),
        max_exams: Optional[int] = Query(None, ge=0, description="Макс. к-сть іспитів"),
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Отримує список курсів, які були створені поточним викладачем.
        """
        self._ensure_role(current_user, {"teacher"}, TEACHER_ONLY_ACCESS)

        items, total = self.service.list_my_courses(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            name_filter=name,
            min_students=min_students,
            max_students=max_students,
            min_exams=min_exams,
            max_exams=max_exams,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def list_courses(
        self,
        name: Optional[str] = Query(None, description=FILTER_NAME_DESCRIPTION),
        teacher_name: Optional[str] = Query(
            None, description="Фільтр за ПІБ або email викладача"
        ),
        min_students: Optional[int] = Query(
            None, ge=0, description=MIN_STUDENTS_DESCRIPTION
        ),
        max_students: Optional[int] = Query(
            None, ge=0, description=MAX_STUDENTS_DESCRIPTION
        ),
        limit: int = Query(100, ge=1, le=100),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Отримує список усіх курсів. Доступно для студентів.
        """
        self._ensure_role(
            current_user,
            {"student"},
            "Цей ендпоінт доступний лише для студентів",
        )

        items, total = self.service.list(
            db=db,
            current_user_id=current_user.id,
            limit=limit,
            offset=offset,
            name_filter=name,
            teacher_filter=teacher_name,
            min_students=min_students,
            max_students=max_students,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def list_courses_for_supervisor(
        self,
        name: Optional[str] = Query(None, description=FILTER_NAME_DESCRIPTION),
        teacher_name: Optional[str] = Query(
            None, description="Фільтр за ПІБ або email викладача (owner)"
        ),
        min_students: Optional[int] = Query(
            None, ge=0, description=MIN_STUDENTS_DESCRIPTION
        ),
        max_students: Optional[int] = Query(
            None, ge=0, description=MAX_STUDENTS_DESCRIPTION
        ),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("supervisor")),
    ):
        """
        Список курсів для наглядача з фільтрами.
        """
        items, _ = self.service.list_for_supervisor(
            db=db,
            current_user=current_user,
            title_filter=name,
            teacher_filter=teacher_name,
            min_students=min_students,
            max_students=max_students,
            limit=limit,
            offset=offset,
        )
        return items

    def get_course_details_for_supervisor(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_role("supervisor")),
    ):
        """
        Деталізована інформація про курс для наглядача.
        """
        return self.service.get_course_details_for_supervisor(
            db, current_user, course_id
        )

    def get_course_analytics(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        self._ensure_role(current_user, {"teacher"}, TEACHER_ONLY_ACCESS)
        return self.service.get_course_exam_statistics(db, course_id)

    def get_group_analytics(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        self._ensure_role(current_user, {"teacher"}, TEACHER_ONLY_ACCESS)
        return self.service.get_group_analytics(db, current_user.id, course_id)

    def create_course(
        self,
        payload: CourseCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        self._ensure_role(
            current_user,
            {"teacher"},
            "Створювати курси можуть лише викладачі",
        )
        return self.service.create(db, payload, owner_id=current_user.id)

    def get_course(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """Отримує деталізовану інформацію про один курс за його ID."""
        return self.service.get(db, course_id)

    def update_course(
        self,
        course_id: UUID,
        patch: CourseUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Оновлює інформацію про курс.
        """
        self._ensure_role(
            current_user,
            {"teacher"},
            "Тільки вчителі можуть оновлювати курси",
        )
        return self.service.update(db, course_id, patch)

    def delete_course(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Видаляє курс за його ID.
        """
        self._ensure_role(
            current_user,
            {"teacher"},
            "Тільки вчителі можуть видаляти курси",
        )
        self.service.delete(db, course_id)
        return None

    def enroll(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Записує поточного студента на курс.
        """
        self._ensure_role(
            current_user,
            {"student"},
            "Записуватись на курси можуть лише студенти",
        )
        self.service.enroll(db, current_user.id, course_id)
        return None

    def unenroll(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Виписує поточного студента з курсу.
        """
        self._ensure_role(
            current_user,
            {"student"},
            "Виписуватись з курсів можуть лише студенти",
        )
        self.service.unenroll(db, current_user.id, course_id)
        return None

    def list_course_exams(
        self,
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_with_role),
    ):
        """
        Отримує список іспитів для курсу. Доступно для викладачів та наглядачів.
        """
        self._ensure_role(
            current_user,
            {"teacher", "supervisor"},
            "Цей функціонал доступний лише для викладачів та наглядачів",
        )
        return self.exams_service.get_exams_for_course(db, course_id=course_id)
