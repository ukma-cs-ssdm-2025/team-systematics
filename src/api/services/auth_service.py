from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.api.repositories.user_repository import UserRepository
from src.core.security import create_access_token
from src.api.schemas.auth import LoginRequest, LoginResponse, UserResponse, RegisterRequest
from src.utils.hashing import verify_password, get_password_hash
from src.models.users import User
from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.majors import Major
from src.models.user_majors import UserMajor


class AuthService:
    def __init__(self):
        self.user_repo = None

    def login(self, db: Session, request: LoginRequest) -> LoginResponse:
        self.user_repo = UserRepository(db)

        user = self.user_repo.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")

        roles = self.user_repo.get_user_roles(str(user.id))
        major_name = self.user_repo.get_user_major(str(user.id))

        token = create_access_token({"sub": str(user.id), "roles": roles})

        return LoginResponse(
            access_token=token,  # Changed from token= to access_token=
            token_type="bearer",  # Added explicit token_type
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=f"{user.first_name} {user.last_name}".strip(),
                user_major=major_name,
                roles=roles,
                avatar_url=user.avatar_url,
            )
        )

    def register(self, db: Session, request: RegisterRequest) -> LoginResponse:
        """Реєстрація нового користувача з роллю 'student' за замовчуванням."""
        self.user_repo = UserRepository(db)

        # Перевіряємо, чи користувач з таким email вже існує
        existing_user = self.user_repo.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з такою електронною поштою вже існує"
            )

        # Створюємо нового користувача
        hashed_password = get_password_hash(request.password)
        new_user = User(
            email=request.email,
            hashed_password=hashed_password,
            first_name=request.first_name,
            last_name=request.last_name,
            patronymic=request.patronymic
        )
        db.add(new_user)
        db.flush()  # Отримуємо ID користувача без коміту транзакції

        # Призначаємо роль 'student' за замовчуванням
        student_role = db.query(Role).filter(Role.name == 'student').first()
        if not student_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Роль 'student' не знайдена в системі"
            )

        user_role = UserRole(user_id=new_user.id, role_id=student_role.id)
        db.add(user_role)

        # Призначаємо спеціальність, якщо вона вказана
        if request.major_id:
            major = db.query(Major).filter(Major.id == request.major_id).first()
            if major:
                user_major = UserMajor(user_id=new_user.id, major_id=major.id)
                db.add(user_major)
            # Якщо major_id вказано, але спеціальність не знайдена - не викидаємо помилку,
            # просто не призначаємо спеціальність

        db.commit()
        db.refresh(new_user)

        # Автоматично логінимо користувача після реєстрації
        roles = self.user_repo.get_user_roles(str(new_user.id))
        major_name = self.user_repo.get_user_major(str(new_user.id))

        token = create_access_token({"sub": str(new_user.id), "roles": roles})

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=str(new_user.id),
                email=new_user.email,
                full_name=f"{new_user.first_name} {new_user.last_name}".strip(),
                user_major=major_name,
                roles=roles,
                avatar_url=new_user.avatar_url,
            )
        )
