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
                emails = _get_student_emails(db)
                for exam in upcoming:
                    already = db.query(ExamEmailNotification).filter(ExamEmailNotification.exam_id == exam.id).first()
                    if already:
                        continue
                    if emails:
                        send_email(
                            subject="Exam reminder",
                            body="Hello World!",
                            recipients=emails,
                        )
                    db.add(ExamEmailNotification(exam_id=exam.id))
                db.commit()
        except Exception:
            # Best-effort scheduler; avoid crashing on errors
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


