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

        @self.router.get("/gpa", response_model=CertificateGpaResponse, summary="Отримати GPA по курсах для поточного користувача")
        async def get_gpa(
            current_user: User = Depends(get_current_user_with_role),
            db: Session = Depends(get_db),
            sort_by: str | None = Query(None, description="Поле для сортування: 'course' або 'gpa'"),
            sort_order: str = Query('asc', description="Порядок сортування: 'asc' або 'desc'"),
        ):
            if current_user.role != 'student':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно лише для студентів")

            # Reuse transcript generation (it already computes per-course ratings)
            transcript = self.service.get_transcript_for_user(current_user.id, db)

            courses = [CourseGpa(id=c.id, course_name=c.course_name, gpa=c.rating) for c in transcript.courses]

            # Apply server-side sorting if requested
            if sort_by:
                sort_by = str(sort_by).lower()
                if sort_by not in ('course', 'gpa'):
                    sort_by = None

            if sort_by:
                reverse = True if str(sort_order).lower() in ('desc', 'descending') else False
                if sort_by == 'course':
                    courses.sort(key=lambda x: (x.course_name or '').lower(), reverse=reverse)
                else:  # gpa
                    # Place None values at the end when ascending
                    def _key(x: CourseGpa):
                        if x.gpa is None:
                            return (1, 0.0)
                        return (0, float(x.gpa))
                    courses.sort(key=_key, reverse=reverse)

            return CertificateGpaResponse(courses=courses)
