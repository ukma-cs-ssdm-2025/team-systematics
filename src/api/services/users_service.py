from fastapi import UploadFile, HTTPException, status
import cloudinary.uploader
import cloudinary.exceptions
from uuid import UUID
from sqlalchemy.orm import Session
from src.models.users import User
from src.api.repositories.user_repository import UserRepository

class UsersService:
    # stateless, __init__ не потрібен

    @staticmethod
    def get_user_profile(user: User) -> dict:
        """Формує дані для відповіді профілю."""
        return {
            "id": user.id,
            "full_name": f"{user.last_name or ''} {user.first_name or ''} {user.patronymic or ''}".strip(),
            "email": user.email,
            "major_name": user.major.name if user.major else "Спеціальність не вказано", 
            "avatar_url": user.avatar_url
        }

    @staticmethod
    def get_notification_settings(user: User) -> dict:
        """Повертає налаштування сповіщень."""
        return user.notification_settings

    @staticmethod
    def update_notification_settings(user_id: UUID, settings_data: dict, db: Session):
        """Оновлює налаштування сповіщень."""
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_repo.update_user_settings(user, 'notification_settings', settings_data)

    @staticmethod
    def update_avatar(user_id: UUID, file: UploadFile, db: Session) -> User:
        """Завантажує аватар в Cloudinary та оновлює URL в профілі."""
        import logging
        logger = logging.getLogger(__name__)
        
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Валідація розміру файлу (максимум 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        file_content = file.file.read()
        file.file.seek(0)  # Повертаємо позицію на початок для подальшого читання
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Валідація типу файлу
        allowed_content_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_content_types)}"
            )
            
        # Генеруємо унікальний public_id для файлу, щоб його можна було перезаписувати
        public_id = f"user_avatars/{user_id}"

        try:
            # Завантажуємо файл в Cloudinary з таймаутом
            upload_result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                overwrite=True,
                timeout=30,  # Таймаут завантаження (секунди)
            )
        except cloudinary.exceptions.Error as e:
            logger.error(f"Cloudinary upload error for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image to cloud service"
            )
        except Exception as e:
            logger.error(f"Unexpected error during avatar upload for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image due to an unexpected error"
            )

        avatar_url = upload_result.get("secure_url")
        if not avatar_url:
            logger.error(f"Cloudinary upload succeeded but no secure_url returned for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get image URL from cloud service"
            )

        return user_repo.update_user_avatar_url(user, avatar_url)