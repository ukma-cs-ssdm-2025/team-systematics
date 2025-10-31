from jose import jwt, JWTError
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import JWT_SECRET, JWT_ALGORITHM
from sqlalchemy.orm import Session, joinedload
from src.api.database import get_db
from src.models.users import User
from src.models.roles import Role
from src.models.user_roles import UserRole

security = HTTPBearer()

class TokenDecodeError(Exception):
    """Викликається, коли JWT не може бути розкодований або є недійсним."""
    pass


def decode_jwt(token: str) -> dict:
    """Розкодовує JWT токен та повертає його вміст (payload).

    Ця функція перевіряє підпис, термін дії та алгоритм токена,
    використовуючи глобально визначені секретний ключ та алгоритм.

    Args:
        token: JWT токен у вигляді рядка, який потрібно розкодувати.

    Returns:
        Словник з даними (claims) токена, якщо валідація успішна.

    Raises:
        TokenDecodeError: Якщо токен недійсний, має невірний підпис,
                          протермінований або не може бути розкодований.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise TokenDecodeError("Failed to decode token") from exc


def get_user_id_from_token(token: str) -> UUID:
    """Видобуває ідентифікатор користувача (`sub`) з JWT токена.

    Функція розкодовує токен, знаходить у його вмісті стандартне поле "sub"
    (subject) і перетворює його на об'єкт UUID.

    Args:
        token: Валідний JWT токен у вигляді рядка.

    Returns:
        Ідентифікатор користувача у форматі UUID.

    Raises:
        TokenDecodeError: Якщо розкодування токена не вдалося, у його вмісті
                          відсутнє поле "sub", або значення цього поля
                          не є валідним UUID.
    """
    payload = decode_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise TokenDecodeError("Token payload missing `sub` claim")
    try:
        return UUID(sub)
    except (ValueError, TypeError) as exc:
        raise TokenDecodeError("Invalid `sub` claim value") from exc


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """Залежність FastAPI для отримання ID поточного користувача з Bearer токена.

    Ця функція-залежність автоматично витягує Bearer токен із заголовка
    `Authorization`, валідує його та повертає ідентифікатор користувача.
    Вона призначена для захисту ендпоінтів, що вимагають автентифікації.

    Returns:
        Ідентифікатор автентифікованого користувача у форматі UUID.

    Raises:
        HTTPException: З кодом 401 UNAUTHORIZED, якщо токен відсутній,
                       пошкоджений, протермінований або не містить
                       коректного ідентифікатора користувача.
    """
    token = credentials.credentials
    try:
        return get_user_id_from_token(token)
    except TokenDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_user_role(db: Session, user_id: UUID) -> str:
    """
    Знаходить та повертає назву ролі для вказаного користувача.
    """
    role_name = db.query(Role.name).join(UserRole).filter(UserRole.user_id == user_id).scalar()
    
    if not role_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no assigned role. Access denied."
        )
        
    return role_name


def get_current_user(db: Session = Depends(get_db), user_id: UUID = Depends(get_current_user_id)) -> User:
    """
    Залежність FastAPI, яка отримує ID користувача з токена,
    завантажує об'єкт користувача, перевіряє наявність ролі та додає
    її як атрибут до об'єкта.
    """
    user = db.query(User).options(
        joinedload(User.major)
    ).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )  
    return user

def get_current_user_with_role(db: Session = Depends(get_db), user_id: UUID = Depends(get_current_user_id)) -> User:
    """
    Завантажує об'єкт користувача та додає до нього атрибут 'role'.
    """
    user = db.query(User).options(
        joinedload(User.major)
    ).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user.role = get_user_role(db, user_id)
    return user