from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query, Header, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.courses import Course, CourseCreate, CourseUpdate, CoursesPage
from src.api.services.courses_service import CoursesService
from src.api.database import get_db
from .versioning import require_api_version


class CoursesController:
    def __init__(self, service: CoursesService) -> None:
        self.service = service
        self.router = APIRouter(
            prefix="/courses",
            tags=["Courses"],
            dependencies=[Depends(require_api_version)],
        )

        # каталог курсів
        @self.router.get(
            "",
            response_model=CoursesPage,
            summary="List courses (catalog)",
        )
        async def list_courses(
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
        ):
            items, total = self.service.list(db, limit, offset)
            return {"items": items, "total": total, "limit": limit, "offset": offset}

        @self.router.post(
            "",
            response_model=Course,
            status_code=status.HTTP_201_CREATED,
            summary="Create course",
        )
        async def create_course(
            payload: CourseCreate,
            db: Session = Depends(get_db),
        ):
            return self.service.create(db, payload)

        @self.router.get(
            "/{course_id}",
            response_model=Course,
            summary="Get course by id",
        )
        async def get_course(
            course_id: int,  
            db: Session = Depends(get_db),
        ):
            return self.service.get(db, course_id)

        @self.router.patch(
            "/{course_id}",
            response_model=Course,
            summary="Update course",
        )
        async def update_course(
            course_id: int,  
            patch: CourseUpdate,
            db: Session = Depends(get_db),
        ):
            return self.service.update(db, course_id, patch)

        @self.router.delete(
            "/{course_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete course",
        )
        async def delete_course(
            course_id: int,  
            db: Session = Depends(get_db),
        ):
            self.service.delete(db, course_id)
            return None

        # запис на курс (DEV: тільки X-User-Id у заголовку) 
        @self.router.post(
            "/{course_id}/enroll",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Enroll current user into a course (DEV via X-User-Id only)",
        )
        async def enroll(
            course_id: int,  
            db: Session = Depends(get_db),
            user_id_header: Optional[UUID] = Header(None, alias="X-User-Id"),
        ):
            if user_id_header is None:
                raise HTTPException(
                    status_code=401,
                    detail="Provide X-User-Id (UUID) header for dev testing",
                )
            self.service.enroll(db, user_id_header, course_id)
            return None

        # мої курси (DEV: тільки X-User-Id у заголовку) 
        @self.router.get(
            "/me/list",
            response_model=CoursesPage,
            summary="List my courses (DEV via X-User-Id only)",
        )
        async def list_my_courses(
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            db: Session = Depends(get_db),
            user_id_header: Optional[UUID] = Header(None, alias="X-User-Id"),
        ):
            if user_id_header is None:
                raise HTTPException(
                    status_code=401,
                    detail="Provide X-User-Id (UUID) header for dev testing",
                )
            items, total = self.service.list_my(db, user_id_header, limit, offset)
            return {"items": items, "total": total, "limit": limit, "offset": offset}