"""
Сервіс для автоматичного оновлення статусів іспитів.
Змінює статус з 'published' на 'open', коли настає час початку іспиту.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.api.database import SessionLocal
from src.models.exams import Exam, ExamStatusEnum

logger = logging.getLogger(__name__)


def update_exam_statuses():
    """
    Перевіряє всі іспити зі статусом 'published' та змінює їх статус на 'open',
    якщо час початку (start_at) вже настав.
    Також змінює статус на 'closed', якщо час завершення (end_at) вже пройшов.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Знаходимо іспити зі статусом 'published', які мають початися
        exams_to_open = db.query(Exam).filter(
            Exam.status == ExamStatusEnum.published,
            Exam.start_at <= now
        ).all()
        
        # Знаходимо іспити зі статусом 'open', які мають завершитися
        exams_to_close = db.query(Exam).filter(
            Exam.status == ExamStatusEnum.open,
            Exam.end_at < now
        ).all()
        
        # Оновлюємо статуси
        opened_count = 0
        for exam in exams_to_open:
            exam.status = ExamStatusEnum.open
            opened_count += 1
            logger.info(f"Exam {exam.id} ({exam.title}) status changed from 'published' to 'open'")
        
        closed_count = 0
        for exam in exams_to_close:
            exam.status = ExamStatusEnum.closed
            closed_count += 1
            logger.info(f"Exam {exam.id} ({exam.title}) status changed from 'open' to 'closed'")
        
        if opened_count > 0 or closed_count > 0:
            db.commit()
            logger.info(f"Updated exam statuses: {opened_count} opened, {closed_count} closed")
        else:
            logger.debug("No exam statuses to update")
            
    except Exception as e:
        logger.error(f"Error updating exam statuses: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

