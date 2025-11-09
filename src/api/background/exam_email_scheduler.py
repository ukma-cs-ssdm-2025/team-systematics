import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from src.api.database import SessionLocal
from src.models.exams import Exam
from src.models.users import User
from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.exam_email_notifications import ExamEmailNotification
from src.utils.emailer import send_email


CHECK_INTERVAL_SECONDS = 60


def _get_student_emails(db: Session):
    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        return []
    q = (
        db.query(User.email)
        .join(UserRole, UserRole.user_id == User.id)
        .filter(UserRole.role_id == student_role.id)
    )
    return [row[0] for row in q.all() if row[0]]

# === НОВА ВИНЕСЕНА ФУНКЦІЯ ===
def _process_upcoming_exams(db: Session, upcoming_exams: list[Exam]):
    """
    Обробляє список майбутніх іспитів, надсилає нагадування
    та позначає їх як оброблені.
    """
    emails = _get_student_emails(db)
    
    for exam in upcoming_exams:
        already_notified = db.query(ExamEmailNotification).filter(
            ExamEmailNotification.exam_id == exam.id
        ).first()
        
        if already_notified:
            continue

        if emails:
            send_email(
                subject="Exam reminder",
                body=f"Нагадування: Іспит '{exam.title}' скоро почнеться.", # В ідеалі тут має бути: body=f"Нагадування: Іспит '{exam.title}' скоро почнеться."
                recipients=emails,
            )
        # Позначаємо іспит як оброблений, навіть якщо не було студентів (щоб не надсилати повторно)
        db.add(ExamEmailNotification(exam_id=exam.id))
    
    # Виконуємо всі зміни в базі даних один раз наприкінці
    db.commit()

async def run_exam_email_scheduler():
    while True:
        try:
            db: Session = SessionLocal()
            now = datetime.now(timezone.utc)
            window_start = now + timedelta(minutes=30)
            window_end = now + timedelta(minutes=31)

            upcoming = (
                db.query(Exam)
                .filter(Exam.start_at >= window_start, Exam.start_at < window_end)
                .all()
            )

            if upcoming:
                # === ОСЬ ТУТ МАЄ БУТИ ВИКЛИК НОВОЇ ФУНКЦІЇ ===
                _process_upcoming_exams(db, upcoming) 
                # === І БІЛЬШЕ НІЧОГО! ===

        except Exception:
            # ...
            pass
        finally:
            # ...
            pass
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)