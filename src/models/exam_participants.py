from enum import Enum
from sqlalchemy import Column, Boolean, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Enum as PgEnum

from src.api.database import Base

class AttendanceStatusEnum(str, Enum):
    unknown = "unknown"
    present = "present"
    absent = "absent"

class ExamParticipant(Base):
    __tablename__ = "exam_participants"

    exam_id   = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    removed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    attendance_status = Column(
        PgEnum(AttendanceStatusEnum, name="attendance_status_enum", create_type=False),
        nullable=False,
        server_default="unknown",
    )
