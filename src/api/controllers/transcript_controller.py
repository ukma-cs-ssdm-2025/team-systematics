from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from src.api.schemas.transcript import TranscriptResponse
from src.api.services.transcript_service import TranscriptService
from src.utils.auth import get_current_user_with_role
from src.api.database import get_db
from src.models.users import User
from typing import Optional
from fastapi import Query

class TranscriptController:
    def __init__(self, service: TranscriptService):
        self.service = service
        self.router = APIRouter(prefix="/transcript", tags=["Transcript"])

        @self.router.get("", response_model=TranscriptResponse, summary="Отримати атестат поточного користувача")
        async def get_transcript(
            current_user: User = Depends(get_current_user_with_role),
            db: Session = Depends(get_db),
            sort_by: Optional[str] = Query(None, description="Поле для сортування (напр., 'rating')"),
            order: str = Query("asc", description="Порядок сортування ('asc' або 'desc')")   
        ):
            """
            Повертає повну інформацію для сторінки "Мій атестат" та загальну статистику.
            Підтримує сортування за полями `course_name`, `rating`, `ects_grade`, `national_grade`, `pass_status`.
            """

            # Перевірка ролі
            if current_user.role != 'student':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Доступно лише для студентів"
                )
            return self.service.get_transcript_for_user(current_user.id, db, sort_by=sort_by, order=order)