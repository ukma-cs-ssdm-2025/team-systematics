from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Literal
from datetime import datetime

class ExamParticipantCreate(BaseModel):
    user_id: UUID = Field(..., description="ID студента, якого додаємо до іспиту")
    course_id: UUID = Field(..., description="ID курсу для перевірки зарахування")

class ExamParticipantAttendanceUpdate(BaseModel):
    status: Literal["present", "absent"] = Field(..., description="Статус присутності студента")

class ExamParticipantResponse(BaseModel):
    exam_id: UUID
    user_id: UUID
    joined_at: datetime | None = None
    removed_at: datetime | None = None
    is_active: bool
    attendance_status: Literal["unknown", "present", "absent"]
