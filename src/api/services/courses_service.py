from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Tuple, List
from src.api.repositories.courses_repository import CoursesRepository
from src.api.schemas.courses import CourseCreate, CourseUpdate
from src.models.courses import Course

class CoursesService:
    def list(self, db: Session, current_user_id: UUID, limit: int, offset: int) -> Tuple[List[Course], int]:
        return CoursesRepository(db).list(current_user_id, limit, offset)

    def get(self, db: Session, course_id: UUID) -> Optional[Course]:
        return CoursesRepository(db).get(course_id)

    def create(self, db: Session, payload: CourseCreate) -> Course:
        return CoursesRepository(db).create(payload)

    def update(self, db: Session, course_id: UUID, patch: CourseUpdate) -> Optional[Course]:
        return CoursesRepository(db).update(course_id, patch)

    def delete(self, db: Session, course_id: UUID) -> None:
        return CoursesRepository(db).delete(course_id)

    def enroll(self, db: Session, user_id, course_id: UUID) -> None:
        return CoursesRepository(db).enroll(user_id, course_id)

    def list_my_courses(self, db: Session, user_id, limit: int, offset: int):
        return CoursesRepository(db).list_my_courses(user_id, limit, offset)
