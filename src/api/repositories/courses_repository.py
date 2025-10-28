from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.models.courses import Course, CourseEnrollment
from src.api.schemas.courses import CourseCreate, CourseUpdate

class CoursesRepository:
    def __init__(self, db: Session):
        self.db = db



    def list(self, limit: int, offset: int) -> Tuple[List[Course], int]:
        total = self.db.query(Course).count()
        items = self.db.query(Course).offset(offset).limit(limit).all()
        return items, total

    def get(self, course_id: UUID) -> Optional[Course]:
        return self.db.query(Course).filter(Course.id == course_id).first()

    def create(self, payload: CourseCreate) -> Course:
        entity = Course(**payload.model_dump())
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, course_id: UUID, patch: CourseUpdate) -> Optional[Course]:
        entity = self.get(course_id)
        if not entity:
            return None
        data = {k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None}
        for k, v in data.items():
            setattr(entity, k, v)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, course_id: UUID) -> None:
        entity = self.get(course_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()



    def enroll(self, user_id, course_id: UUID) -> None:
        # idempotent: do nothing if already enrolled
        exists = (
            self.db.query(CourseEnrollment)
            .filter(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id)
            .first()
        )
        if exists:
            return
        self.db.add(CourseEnrollment(user_id=user_id, course_id=course_id))
        self.db.commit()

    def list_my(self, user_id, limit: int, offset: int) -> Tuple[List[Course], int]:
        q = (
            self.db.query(Course)
            .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
            .filter(CourseEnrollment.user_id == user_id)
        )
        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return items, total
