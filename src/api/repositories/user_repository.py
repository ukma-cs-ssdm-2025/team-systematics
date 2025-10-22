from sqlalchemy.orm import Session
from src.models.users import User
from src.models.roles import Role
from src.models.userRoles import UserRole


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
