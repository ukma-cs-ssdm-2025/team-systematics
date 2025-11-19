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


# Як часто перевіряти базу (раз на хвилину достатньо)
CHECK_INTERVAL_SECONDS = 60

# Опції сповіщень (у годинах), які підтримує система
NOTIFICATION_WINDOWS = [1, 8, 24]


def _get_students_for_window(db: Session, hours: int) -> List[str]:
    """
    Повертає email-адреси студентів, які:
    1. Мають увімкнені сповіщення (enabled: true).
    2. Обрали конкретний інтервал (hours) у списку remind_before_hours.
    """
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return []
    
    # Формуємо запит до JSONB
    # notification_settings -> 'remind_before_hours' має містити число `hours`
    q = (
        db.query(User.email)
        .join(UserRole, UserRole.user_id == User.id)
        .filter(UserRole.role_id == student_role.id)
        # Перевіряємо глобальний перемикач (чи enabled == true)
        .filter(User.notification_settings['enabled'].astext == 'true')
        # Перевіряємо наявність числа в масиві remind_before_hours
        .filter(User.notification_settings['remind_before_hours'].contains([hours]))
    )
    
    return [row[0] for row in q.all() if row[0]]


def _process_window(db: Session, hours: int):
    """
    Знаходить іспити, що починаються через `hours` годин, 
    і надсилає сповіщення відповідним студентам.
    """
    now = datetime.now(timezone.utc)
    
    # Вікно перевірки: Іспит починається через X годин (плюс 1 хвилина буфера)
    window_start = now + timedelta(hours=hours)
    window_end = window_start + timedelta(minutes=1)
    
    upcoming_exams = (
        db.query(Exam)
        .filter(Exam.start_at >= window_start, Exam.start_at < window_end)
        .all()
    )

    if not upcoming_exams:
        return

    # Отримуємо підписників саме для цього інтервалу
    emails = _get_students_for_window(db, hours)
    
    if not emails:
        return

    for exam in upcoming_exams:
        # Перевіряємо, чи ми вже надсилали сповіщення "за X годин" для цього іспиту
        already_notified = db.query(ExamEmailNotification).filter_by(
            exam_id=exam.id,
            hours_before=hours
        ).first()
        
        if already_notified:
            continue

        # Формуємо текст залежно від часу
        if hours == 1:
            time_text = "1 годину"
        elif hours % 24 == 0:
            days = hours // 24
            time_text = f"{days} день/дні"
        else:
            time_text = f"{hours} годин(и)"

        send_email(
            subject=f"Нагадування про іспит: {exam.title}",
            body=f"Вітаємо! Нагадуємо, що іспит '{exam.title}' розпочнеться через {time_text}.",
            recipients=emails,
        )
        
        # Записуємо в базу, що для цього інтервалу сповіщення відправлено
        db.add(ExamEmailNotification(exam_id=exam.id, hours_before=hours))
    
    db.commit()


async def run_exam_email_scheduler():
    """
    Основний цикл планувальника. Перевіряє всі часові вікна.
    """
    while True:
        db: Session | None = None
        try:
            db = SessionLocal()
            
            # Перевіряємо кожне вікно (1, 8, 24 години) окремо
            for hours in NOTIFICATION_WINDOWS:
                _process_window(db, hours)

        except Exception as e:
            print(f"Scheduler error: {e}")
        finally:
            if db:
                db.close()
                
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)