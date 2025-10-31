from sqlalchemy.orm import Session
from uuid import UUID
from src.models.users import User
from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.majors import Major
from src.models.user_majors import UserMajor


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_user_roles(self, user_id: str):
        roles = (
            self.db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return [r[0] for r in roles]

    def get_user_major(self, user_id: str) -> str:
        """
        Отримує назву спеціальності користувача за його ID.
        """
        major = (
            self.db.query(Major.name)
            .join(UserMajor, UserMajor.major_id == Major.id)
            .filter(UserMajor.user_id == user_id)
            .first()
        )
        return major[0] if major else None

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Знаходить користувача за його ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user_settings(self, user: User, settings_field: str, settings_data: dict) -> User:
        """
        Універсальний метод для оновлення JSONB полів користувача.
        
        Args:
            user: Об'єкт користувача SQLAlchemy.
            settings_field: Назва атрибута для оновлення (напр., 'notification_settings').
            settings_data: Словник з новими налаштуваннями.
        """
        setattr(user, settings_field, settings_data)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_avatar_url(self, user: User, avatar_url: str) -> User:
        """Оновлює URL аватара для користувача."""
        user.avatar_url = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user