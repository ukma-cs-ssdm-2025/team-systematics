from sqlalchemy.orm import Session
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