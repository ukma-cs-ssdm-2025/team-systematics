from sqlalchemy import Column, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from src.api.database import Base


class ExamEmailNotification(Base):
    __tablename__ = "exam_email_notifications"

    exam_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    sent_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False)


