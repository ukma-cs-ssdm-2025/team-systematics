from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from src.models.courses import Course, CourseEnrollment
from src.models.course_exams import CourseExam
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

    def list_my_courses(self, teacher_id: UUID, limit: int, offset: int):
        student_count_subquery = (
            self.db.query(CourseEnrollment.course_id, func.count(CourseEnrollment.user_id).label("student_count"))
            .group_by(CourseEnrollment.course_id).subquery()
        )
        exam_count_subquery = (
            self.db.query(CourseExam.course_id, func.count(CourseExam.exam_id).label("exam_count"))
            .group_by(CourseExam.course_id).subquery()
        )

        query = self.db.query(
            Course,
            student_count_subquery.c.student_count,
            exam_count_subquery.c.exam_count
        ).outerjoin(
            student_count_subquery, Course.id == student_count_subquery.c.course_id
        ).outerjoin(
            exam_count_subquery, Course.id == exam_count_subquery.c.course_id
        ).filter(Course.owner_id == teacher_id)

        total = query.count()
        results = query.order_by(Course.name).limit(limit).offset(offset).all()

        items = [
            {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "student_count": student_count or 0,
                "exam_count": exam_count or 0
            } for course, student_count, exam_count in results
        ]
        return items, total
