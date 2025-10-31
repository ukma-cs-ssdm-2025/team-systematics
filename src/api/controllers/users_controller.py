from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from src.models.users import User
from src.api.database import get_db
from src.utils.auth import get_current_user
from src.api.services.users_service import UserService
from src.api.schemas.users import UserProfileResponse, NotificationSettingsSchema, AvatarUpdateResponse

class UsersController:
    def __init__(self, service: UserService):
        self.service = service
        self.router = APIRouter(prefix="/users", tags=["User Profile"])

        @self.router.get(
            "/me", 
            response_model=UserProfileResponse, 
            summary="Отримати профіль поточного користувача"
        )
        async def get_me(current_user: User = Depends(get_current_user)):
            """Повертає публічну інформацію профілю для автентифікованого користувача."""
            return self.service.get_user_profile(current_user)

        @self.router.get(
            "/me/notifications", 
            response_model=NotificationSettingsSchema, 
            summary="Отримати налаштування сповіщень"
        )
        async def get_my_notifications(current_user: User = Depends(get_current_user)):
            """Повертає поточні налаштування сповіщень користувача."""
            return self.service.get_notification_settings(current_user)

        @self.router.put(
            "/me/notifications",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Оновити налаштування сповіщень"
        )
        async def update_my_notifications(
            settings: NotificationSettingsSchema,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Приймає та зберігає нові налаштування сповіщень для користувача."""
            self.service.update_notification_settings(
                user_id=current_user.id,
                settings_data=settings.model_dump(),
                db=db
            )
            return None

        @self.router.post(
            "/me/avatar",
            response_model=AvatarUpdateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Завантажити або оновити аватар"
        )
        async def upload_my_avatar(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            avatar_file: UploadFile = File(...) 
        ):
            """Приймає файл зображення, завантажує його в хмарне сховище
            та оновлює посилання на аватар у профілі користувача."""
            updated_user = self.service.update_avatar(current_user.id, avatar_file, db)
            return {"avatar_url": updated_user.avatar_url}