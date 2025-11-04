from typing import Optional, Literal, Callable
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.api.schemas.certificate import CertificateGpaResponse, CourseGpa
from src.api.services.transcript_service import TranscriptService
from src.utils.auth import get_current_user_with_role
from src.api.database import get_db
from src.models.users import User


class CertificateController:
    def __init__(self, transcript_service: TranscriptService):
        self.service = transcript_service
        self.router = APIRouter(prefix="/certificate", tags=["Certificate"])

        @self.router.get(
            "/gpa",
            response_model=CertificateGpaResponse,
            summary="Отримати GPA по курсах для поточного користувача",
        )
        async def get_gpa(
            current_user: User = Depends(get_current_user_with_role),
            db: Session = Depends(get_db),
            sort_by: Optional[Literal["course", "gpa"]] = Query(
                None, description="Поле для сортування: 'course' або 'gpa'"
            ),
            sort_order: Literal["asc", "desc"] = Query(
                "asc", description="Порядок сортування: 'asc' або 'desc'"
            ),
        ):
            self._ensure_student(current_user)

            transcript = self.service.get_transcript_for_user(current_user.id, db)
            courses = [CourseGpa(id=c.id, course_name=c.course_name, gpa=c.rating)
                       for c in transcript.courses]

            if sort_by:
                self._sort_courses(courses, sort_by, sort_order)

            return CertificateGpaResponse(courses=courses)

    @staticmethod
    def _ensure_student(user: User) -> None:
        if user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступно лише для студентів",
            )

    @staticmethod
    def _sort_courses(
        courses: list[CourseGpa],
        sort_by: Literal["course", "gpa"],
        sort_order: Literal["asc", "desc"],
    ) -> None:
        reverse = sort_order == "desc"

        def course_key(x: CourseGpa):
            return (x.course_name or "").lower()

        def gpa_key(x: CourseGpa):
            # None завжди в кінці при 'asc' і на початку при 'desc' — керує reverse
            return (x.gpa is None, float(x.gpa or 0.0))

        key_map: dict[str, Callable[[CourseGpa], tuple | str | float]] = {
            "course": course_key,
            "gpa": gpa_key,
        }
        courses.sort(key=key_map[sort_by], reverse=reverse)
