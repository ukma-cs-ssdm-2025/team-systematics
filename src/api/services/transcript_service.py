from typing import Optional, Literal
from uuid import UUID
import math
from collections import defaultdict
from sqlalchemy.orm import Session

from src.api.repositories.transcript_repository import TranscriptRepository
from src.api.schemas.transcript import TranscriptResponse, CourseResult, Statistics


class TranscriptService:
    # (не обов'язково, але теж трохи зменшує складність у класі)
    def _convert_rating_to_grades(self, rating: float) -> tuple[str, str]:
        # межі від вищої до нижчої, перше співпадіння – відповідь
        bands = [
            (90, 100, "A",  "Відмінно"),
            (82,  89,  "B",  "Добре"),
            (75,  81,  "C",  "Добре"),
            (64,  74,  "D",  "Задовільно"),
            (60,  63,  "E",  "Задовільно"),
            (35,  59,  "FX", "Незадовільно"),
        ]
        for lo, hi, ects, nat in bands:
            if lo <= rating <= hi:
                return ects, nat
        return "F", "Незадовільно"

    def get_transcript_for_user(
        self,
        user_id: UUID,
        db: Session,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> TranscriptResponse:
        repo = TranscriptRepository(db)
        exams = repo.get_all_exams()
        attempts = repo.get_all_attempts_by_user(user_id)

        max_scores = self._max_score_by_exam(attempts)
        courses, completed_cnt, a_cnt, raw_sum = self._build_course_results(exams, max_scores)

        if sort_by:
            self._sort_courses(courses, sort_by, sort_order)

        stats = self._compute_statistics(
            total_exams=len(exams),
            completed=completed_cnt,
            a_grades=a_cnt,
            raw_sum=raw_sum,
        )
        return TranscriptResponse(courses=courses, statistics=stats)

    # ---------- helpers ----------

    @staticmethod
    def _max_score_by_exam(user_attempts) -> dict:
        """Повертає максимальні набрані бали по кожному екзамену користувача."""
        max_scores = defaultdict(float)
        for a in user_attempts:
            if a.earned_points is not None:
                if a.earned_points > max_scores[a.exam_id]:
                    max_scores[a.exam_id] = a.earned_points
        return max_scores

    def _build_course_results(self, exams, max_scores: dict) -> tuple[list[CourseResult], int, int, float]:
        """
        Створює список CourseResult і паралельно рахує:
        - кількість завершених курсів,
        - кількість 'A',
        - суму сирих (неокруглених) рейтингів для середнього.
        """
        results: list[CourseResult] = []
        completed = 0
        a_count = 0
        raw_sum = 0.0

        for exam in exams:
            raw = max_scores.get(exam.id)
            if raw is None:
                results.append(CourseResult(
                    id=exam.id,
                    course_name=exam.title,
                    rating=None,
                    ects_grade=None,
                    national_grade=None,
                    pass_status=None,
                ))
                continue

            final_rating = math.ceil(raw)
            ects, nat = self._convert_rating_to_grades(final_rating)
            pass_status = "Так" if final_rating >= exam.pass_threshold else "Ні"

            results.append(CourseResult(
                id=exam.id,
                course_name=exam.title,
                rating=final_rating,
                ects_grade=ects,
                national_grade=nat,
                pass_status=pass_status,
            ))

            completed += 1
            raw_sum += raw
            if ects == "A":
                a_count += 1

        return results, completed, a_count, raw_sum

    @staticmethod
    def _sort_courses(
        courses: list[CourseResult],
        sort_by: str,
        sort_order: Literal["asc", "desc", "ascending", "descending", "-1"] = "asc",
    ) -> None:
        allowed = {"course_name", "rating", "ects_grade", "national_grade", "pass_status"}
        if sort_by not in allowed:
            return

        reverse = str(sort_order).lower() in ("desc", "descending", "-1")

        def key_course(x: CourseResult):
            return (x.course_name or "").lower()

        def key_rating(x: CourseResult):
            # None завжди в кінці (через перший елемент кортежу)
            return (x.rating is None, float(x.rating or 0.0))

        def key_str(attr: str):
            return lambda x: (getattr(x, attr) is None, str(getattr(x, attr) or "").lower())

        key_map = {
            "course_name": key_course,
            "rating": key_rating,
            "ects_grade": key_str("ects_grade"),
            "national_grade": key_str("national_grade"),
            "pass_status": key_str("pass_status"),
        }
        courses.sort(key=key_map[sort_by], reverse=reverse)

    @staticmethod
    def _compute_statistics(
        total_exams: int,
        completed: int,
        a_grades: int,
        raw_sum: float,
    ) -> Statistics:
        raw_avg = (raw_sum / completed) if completed else 0.0
        final_avg = math.ceil(raw_avg)
        return Statistics(
            completed_courses=completed,
            total_courses=total_exams,
            a_grades_count=a_grades,
            average_rating=final_avg,
        )
