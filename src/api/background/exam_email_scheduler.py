import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from src.api.database import SessionLocal
from src.models.exams import Exam
from src.models.users import User
from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.exam_email_notifications import ExamEmailNotification
from src.utils.emailer import send_email


# Інтервал, з яким планувальник перевіряє базу даних (60 секунд = 1 хвилина)
CHECK_INTERVAL_SECONDS = 60
# Час до іспиту, за який потрібно надіслати сповіщення (30 хвилин)
NOTIFICATION_TIME_MINUTES = 30


def _get_student_emails(db: Session) -> List[str]:
    """
    Повертає список email-адрес усіх користувачів з роллю 'student'.
    """
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return []
    
    # Запит обирає email користувачів, які мають роль 'student'
    q = (
        db.query(User.email)
        .join(UserRole, UserRole.user_id == User.id)
        .filter(UserRole.role_id == student_role.id)
    )
    # Повертає список email-адрес
    return [row[0] for row in q.all() if row[0]]


def _process_upcoming_exams(db: Session, upcoming_exams: List[Exam]):
    """
    Обробляє список майбутніх іспитів, надсилає нагадування
    та позначає їх як оброблені.
    """
    # Отримуємо список усіх студентських email'ів
    emails = _get_student_emails(db)
    
    for exam in upcoming_exams:
        # Перевіряємо, чи вже було надіслано сповіщення для цього іспиту
        already_notified = db.query(ExamEmailNotification).filter(
            ExamEmailNotification.exam_id == exam.id
        ).first()
        
        if already_notified:
            continue

        if emails:
            send_email(
                subject="Exam reminder",
                body=f"Нагадування: Іспит '{exam.title}' скоро почнеться.",
                recipients=emails,
            )
        
        # Позначаємо іспит як оброблений, навіть якщо не було email'ів
        db.add(ExamEmailNotification(exam_id=exam.id))
    
    # Виконуємо всі зміни в базі даних
    db.commit()


async def run_exam_email_scheduler():
    """
    Основний цикл планувальника, який працює у фоновому режимі.
    """
    while True:
        db: Session | None = None
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)
            
            # Визначаємо часове вікно: від 30 до 31 хвилини до іспиту
            window_start = now + timedelta(minutes=NOTIFICATION_TIME_MINUTES)
            window_end = now + timedelta(minutes=NOTIFICATION_TIME_MINUTES + 1) # +1 хвилина = 60 секунд
            
            # Знаходимо іспити, що потрапляють у це вікно
            upcoming = (
                db.query(Exam)
                .filter(Exam.start_at >= window_start, Exam.start_at < window_end)
                .all()
            )

            if upcoming:
                _process_upcoming_exams(db, upcoming) 

        except Exception as e:
            # Логування помилки
            print(f"An error occurred in the scheduler: {e}")
            pass
        finally:
            if db:
                db.close()
                
        # Чекаємо наступного інтервалу
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)