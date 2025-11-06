from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from src.models.users import User
from src.api.schemas.courses import Course, CourseBase, CourseCreate, CourseUpdate, CoursesPage
from src.api.services.courses_service import CoursesService
from src.api.database import get_db
from src.utils.auth import get_current_user_with_role, get_current_user
from .versioning import require_api_version

class CoursesController:
    def __init__(self, service: CoursesService) -> None:
        self.service = service
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
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user_with_role),
        ):
            """
            Отримує список курсів, які були створені поточним автентифікованим
            викладачем. Повертає дані з пагінацією та додатковою статистикою
            (кількість студентів та іспитів).

            Доступно лише для користувачів з роллю 'teacher'.
            """
            if current_user.role != 'teacher':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Цей функціонал доступний лише для викладачів",
                )
            # Припускаємо, що сервіс має метод list_my_courses або list_teaching
            items, total = self.service.list_my_courses(db, current_user.id, limit, offset) 
            return {"items": items, "total": total, "limit": limit, "offset": offset}

        @self.router.get(
            "",
            response_model=CoursesPage,
            summary="Каталог усіх курсів",
        )
        async def list_courses(
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            """
            Повертає загальний список усіх доступних курсів у системі
            з пагінацією.
            """
            items, total = self.service.list(db, current_user_id=current_user.id, limit=limit, offset=offset)
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