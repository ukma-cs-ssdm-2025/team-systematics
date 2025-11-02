from fastapi import UploadFile, HTTPException, status
import cloudinary.uploader
from uuid import UUID
from sqlalchemy.orm import Session
from src.models.users import User
from src.api.repositories.user_repository import UserRepository

class UsersService:
    # stateless, __init__ не потрібен

    def get_user_profile(self, user: User) -> dict:
        """Формує дані для відповіді профілю."""
        return {
            "full_name": f"{user.last_name or ''} {user.first_name or ''} {user.patronymic or ''}".strip(),
            "email": user.email,
            "major_name": user.major.name if user.major else "Спеціальність не вказано", 
            "avatar_url": user.avatar_url
        }

    def get_notification_settings(self, user: User) -> dict:
        """Повертає налаштування сповіщень."""
        return user.notification_settings

    def update_notification_settings(self, user_id: UUID, settings_data: dict, db: Session):
        """Оновлює налаштування сповіщень."""
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_repo.update_user_settings(user, 'notification_settings', settings_data)

    def update_avatar(self, user_id: UUID, file: UploadFile, db: Session) -> User:
        """Завантажує аватар в Cloudinary та оновлює URL в профілі."""
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
        # Генеруємо унікальний public_id для файлу, щоб його можна було перезаписувати
        public_id = f"user_avatars/{user_id}"

        try:
            # Завантажуємо файл в Cloudinary
            upload_result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                overwrite=True,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload image: {e}")

        avatar_url = upload_result.get("secure_url")
        if not avatar_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get image URL from cloud service.")

        return user_repo.update_user_avatar_url(user, avatar_url)