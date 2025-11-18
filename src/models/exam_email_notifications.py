from sqlalchemy import Column, TIMESTAMP, Integer, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from src.api.database import Base


class ExamEmailNotification(Base):
    """
    Модель для відстеження надісланих сповіщень про іспити.
    Зберігає пару (іспит, час_до_початку), щоб не надсилати дублікати.
    """
    __tablename__ = "exam_email_notifications"

    # Композитний первинний ключ: іспит + тип сповіщення (за скільки годин)
    exam_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    hours_before = Column(Integer, primary_key=True)  # Наприклад: 1, 8 або 24
    
    sent_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False)