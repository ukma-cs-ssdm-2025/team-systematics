from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from src.api.schemas.transcript import TranscriptResponse
from src.api.services.transcript_service import TranscriptService
from src.utils.auth import get_current_user
from src.api.database import get_db
from src.models.users import User

class TranscriptController:
    def __init__(self, service: TranscriptService):
        self.service = service
        self.router = APIRouter(prefix="/transcript", tags=["Transcript"])

        @self.router.get("", response_model=TranscriptResponse, summary="Отримати атестат поточного користувача")
        async def get_transcript( current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
            """
            Повертає повну інформацію для сторінки "Мій атестат",
            включаючи список всіх курсів з найкращими оцінками та
            загальну статистику.
            """
            # Перевірка ролі
            if current_user.role != 'student':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Доступно лише для студентів"
                )
            return self.service.get_transcript_for_user(current_user.id, db)