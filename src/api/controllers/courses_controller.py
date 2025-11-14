from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.analytics import CourseAnalyticsResponse, GroupScoreAnalytics
from src.models.users import User
from src.api.schemas.exams import CourseExamsPage
from src.api.schemas.courses import Course, CourseBase, CourseCreate, CourseUpdate, CoursesPage
from src.api.services.courses_service import CoursesService
from src.api.services.exams_service import ExamsService 
from src.api.database import get_db
from src.utils.auth import get_current_user_with_role, get_current_user, require_role
from .versioning import require_api_version
from src.api.schemas.courses import CourseSupervisorListItem, CourseSupervisorDetails

TEACHER_ONLY_ACCESS = "Цей функціонал доступний лише для викладачів"
# Константи для описів параметрів запиту
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

        @self.router.get(
            "/me",
            response_model=CoursesPage,
            summary="Список моїх курсів (лише для викладача)",
        )
        async def list_my_courses(
            name: Optional[str] = Query(None, description=FILTER_NAME_DESCRIPTION),
            min_students: Optional[int] = Query(None, ge=0, description=MIN_STUDENTS_DESCRIPTION),
            max_students: Optional[int] = Query(None, ge=0, description=MAX_STUDENTS_DESCRIPTION),
            min_exams: Optional[int] = Query(None, ge=0, description="Мін. к-сть іспитів"),
            max_exams: Optional[int] = Query(None, ge=0, description="Макс. к-сть іспитів"),
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Отримує список курсів, які були створені поточним автентифікованим
            викладачем. Повертає дані з пагінацією та додатковою статистикою
            (кількість студентів та іспитів) з підтримкою фільтрації.

            Доступно лише для користувачів з роллю 'teacher'.
            """
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=TEACHER_ONLY_ACCESS,
                )
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

        @self.router.post(
            "",
            response_model=CourseBase,
            status_code=status.HTTP_201_CREATED,
            summary="Створити новий курс (лише для викладача)",
        )
        async def create_course(
            payload: CourseCreate,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Створює новий курс. Власником курсу автоматично стає
            поточний автентифікований викладач.

            Доступно лише для користувачів з роллю 'teacher'.
            """
            if current_user.role != 'teacher':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Створювати курси можуть лише викладачі")
            return self.service.create(db, payload, owner_id=current_user.id)

        @self.router.get("/{course_id}", response_model=Course)
        async def get_course(course_id: UUID, db: Session = Depends(get_db)):
            """Отримує деталізовану інформацію про один курс за його ID."""
            return self.service.get(db, course_id)

        @self.router.patch("/{course_id}", response_model=Course)
        async def update_course(course_id: UUID, patch: CourseUpdate, db: Session = Depends(get_db)):
            """
            Оновлює інформацію про курс. Дозволяє часткове оновлення полів.
            (Примітка: має бути реалізована перевірка власності курсу).
            """
            return self.service.update(db, course_id, patch)
        
        @self.router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_course(course_id: UUID, db: Session = Depends(get_db)):
            """
            Видаляє курс за його ID.
            (Примітка: має бути реалізована перевірка власності курсу).
            """
            self.service.delete(db, course_id)
            return None

        @self.router.post("/{course_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
        async def enroll(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Записує поточного автентифікованого студента на вказаний курс.

            Доступно лише для користувачів з роллю 'student'.
            """
            if current_user.role != 'student':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Записуватись на курси можуть лише студенти")
            self.service.enroll(db, current_user.id, course_id)
            return None
        
        @self.router.get(
            "/{course_id}/exams",
            response_model=CourseExamsPage,
            summary="Список іспитів для курсу (лише для викладача)",
        )
        async def list_course_exams(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Отримує список всіх іспитів, пов'язаних з конкретним курсом,
            разом з розширеною статистикою по кожному іспиту.
            Лише для вчителів.
            """
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=TEACHER_ONLY_ACCESS,
                )
            
            return self.exams_service.get_exams_for_course(db, course_id=course_id)
        
        # Важливо: маршрути /supervisor мають бути перед /{course_id}
        # щоб FastAPI не інтерпретував "supervisor" як UUID
        @self.router.get(
            "/supervisor",
            response_model=list[CourseSupervisorListItem],
            summary="Список курсів для наглядача",
        )
        async def list_courses_for_supervisor(
            name: Optional[str] = Query(None, description=FILTER_NAME_DESCRIPTION),
            teacher_name: Optional[str] = Query(
                None, description="Фільтр за ПІБ або email викладача (owner)"
            ),
            min_students: Optional[int] = Query(None, ge=0, description=MIN_STUDENTS_DESCRIPTION),
            max_students: Optional[int] = Query(None, ge=0, description=MAX_STUDENTS_DESCRIPTION),
            limit: int = Query(50, ge=1, le=200),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
            current_user: User = Depends(require_role('supervisor')),
        ):
            """
            Повертає список курсів для наглядача з фільтрами (назва/викладач/к-сть студентів).
            Перевірка ролі 'supervisor' виконується в сервісі.
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

        @self.router.get(
            "/supervisor/{course_id}",
            response_model=CourseSupervisorDetails,
            summary="Деталі курсу для наглядача",
        )
        async def get_course_details_for_supervisor(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(require_role('supervisor')),
        ):
            """
            Повертає детальну інформацію про курс для наглядача:
            списки студентів (ім'я, email, статус) та викладачів.
            Якщо немає зареєстрованих користувачів — повертається повідомлення.
            Перевірка ролі 'supervisor' виконується в сервісі.
            """
            return self.service.get_course_details_for_supervisor(db, current_user, course_id)

        @self.router.get("/{course_id}/analytics", response_model=CourseAnalyticsResponse, summary="Аналітика курсу: статистика по іспитах")
        async def get_course_analytics(course_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
            if current_user.role != 'teacher':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=TEACHER_ONLY_ACCESS)
            course_stats = self.service.get_course_exam_statistics(db, course_id)
            return course_stats

        @self.router.get("/{course_id}/group-analytics", response_model=GroupScoreAnalytics, summary="Аналітика групи: середній/мін/макс/медіана оцінок")
        async def get_group_analytics(course_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role)):
            if current_user.role != 'teacher':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=TEACHER_ONLY_ACCESS)
            return self.service.get_group_analytics(db, current_user.id, course_id)

        @self.router.post(
            "",
            response_model=CourseBase,
            status_code=status.HTTP_201_CREATED,
            summary="Створити новий курс (лише для викладача)",
        )
        async def create_course(
            payload: CourseCreate,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Створює новий курс. Власником курсу автоматично стає
            поточний автентифікований викладач.

            Доступно лише для користувачів з роллю 'teacher'.
            """
            if current_user.role != 'teacher':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Створювати курси можуть лише викладачі")
            return self.service.create(db, payload, owner_id=current_user.id)

        @self.router.get("/{course_id}", response_model=Course)
        async def get_course(
            course_id: UUID, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            """Отримує деталізовану інформацію про один курс за його ID."""
            # Перевірка ролі: всі автентифіковані користувачі можуть переглядати курси
            return self.service.get(db, course_id)

        @self.router.patch("/{course_id}", response_model=Course)
        async def update_course(
            course_id: UUID, 
            patch: CourseUpdate, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            """
            Оновлює інформацію про курс. Дозволяє часткове оновлення полів.
            (Примітка: має бути реалізована перевірка власності курсу).
            """
            # Перевірка ролі: тільки вчитель може оновлювати курси
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть оновлювати курси"
                )
            return self.service.update(db, course_id, patch)
        
        @self.router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_course(
            course_id: UUID, 
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role)
        ):
            """
            Видаляє курс за його ID.
            (Примітка: має бути реалізована перевірка власності курсу).
            """
            # Перевірка ролі: тільки вчитель може видаляти курси
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Тільки вчителі можуть видаляти курси"
                )
            self.service.delete(db, course_id)
            return None

        @self.router.post("/{course_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
        async def enroll(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Записує поточного автентифікованого студента на вказаний курс.

            Доступно лише для користувачів з роллю 'student'.
            """
            if current_user.role != 'student':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Записуватись на курси можуть лише студенти")
            self.service.enroll(db, current_user.id, course_id)
            return None
        
        @self.router.delete("/{course_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
        async def unenroll(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Виписує поточного автентифікованого студента з вказаного курсу.

            Доступно лише для користувачів з роллю 'student'.
            """
            if current_user.role != 'student':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Виписуватись з курсів можуть лише студенти")
            self.service.unenroll(db, current_user.id, course_id)
            return None
        
        @self.router.get(
            "/{course_id}/exams",
            response_model=CourseExamsPage,
            summary="Список іспитів для курсу (для викладача та наглядача)",
        )
        async def list_course_exams(
            course_id: UUID,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Отримує список всіх іспитів, пов'язаних з конкретним курсом,
            разом з розширеною статистикою по кожному іспиту.
            Доступно для викладачів та наглядачів.
            """
            if current_user.role not in ['teacher', 'supervisor']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для викладачів та наглядачів",
                )
            
            return self.exams_service.get_exams_for_course(db, course_id=course_id)
