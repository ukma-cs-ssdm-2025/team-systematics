from uuid import UUID
import math
from sqlalchemy.orm import Session
from collections import defaultdict
from src.api.repositories.transcript_repository import TranscriptRepository
from src.api.schemas.transcript import TranscriptResponse, CourseResult, Statistics
from typing import List, Optional

class TranscriptService:
    @staticmethod
    def _convert_rating_to_grades(rating: float) -> tuple[str, str]:
        if 90 <= rating <= 100:
            return ("A", "Відмінно")
        elif 82 <= rating <= 89:
            return ("B", "Добре")
        elif 75 <= rating <= 81:
            return ("C", "Добре")
        elif 64 <= rating <= 74:
            return ("D", "Задовільно")
        elif 60 <= rating <= 63:
            return ("E", "Задовільно")
        elif 35 <= rating <= 59:
            return ("FX", "Незадовільно")
        else: # 1-34
            return ("F", "Незадовільно")

    @staticmethod
    def _sort_results(results: List[CourseResult], sort_by: str, order: str) -> List[CourseResult]:
        """
        Сортує список результатів курсів за вказаним полем та напрямком.
        Значення None завжди розміщуються в кінці списку.
        """
        reverse_order = (order == "desc")
            
        def sort_key(course_result):
            value = getattr(course_result, sort_by, None)
            if value is None:
                return (float('inf'),) if order == 'asc' else (float('-inf'),)
            return (0, value)

        results.sort(key=sort_key, reverse=reverse_order)
        return results

    def get_transcript_for_user(
            self, 
            user_id: UUID,
            db: Session,
            sort_by: Optional[str] = None,
            order: str = "asc"
        )-> TranscriptResponse:

        repository = TranscriptRepository(db)
        
        students_exams = repository.get_exams_for_student(user_id)
        user_attempts = repository.get_all_attempts_by_user(user_id)

        max_scores = defaultdict(float)
        for attempt in user_attempts:
            if attempt.earned_points is not None:
                current_max = max_scores[attempt.exam_id]
                max_scores[attempt.exam_id] = max(current_max, attempt.earned_points)

        course_results: list[CourseResult] = []
        completed_courses_count = 0
        a_grades_count = 0
        # Сумуємо не заокруглені бали для точності середнього
        total_raw_rating_sum = 0.0

        for exam in students_exams:
            if exam.id in max_scores:
                # Отримуємо точний, не заокруглений рейтинг
                raw_rating = max_scores[exam.id]
                
                # Заокруглюємо індивідуальний рейтинг вгору
                final_rating = math.ceil(raw_rating)
                
                ects_grade, national_grade = self._convert_rating_to_grades(final_rating)
                pass_status = "Так" if final_rating >= exam.pass_threshold else "Ні"
                
                course_results.append(CourseResult(
                    id=exam.id,
                    course_name=exam.title,
                    rating=final_rating, 
                    ects_grade=ects_grade,
                    national_grade=national_grade,
                    pass_status=pass_status
                ))
                
                completed_courses_count += 1
                total_raw_rating_sum += raw_rating
                if ects_grade == "A":
                    a_grades_count += 1
            else:
                course_results.append(CourseResult(
                    id=exam.id,
                    course_name=exam.title,
                    rating=None, ects_grade=None, national_grade=None, pass_status=None
                ))

        # Рахуємо точний середній рейтинг
        raw_average_rating = (total_raw_rating_sum / completed_courses_count) if completed_courses_count > 0 else 0.0
        
        # Заокруглюємо фінальний середній рейтинг ВГОРУ
        final_average_rating = math.ceil(raw_average_rating)

        # Якщо передано параметри сортування, то сортуємо за ними
        if sort_by:
            course_results = self._sort_results(course_results, sort_by, order)
        
        statistics = Statistics(
            completed_courses=completed_courses_count,
            total_courses=len(students_exams),
            a_grades_count=a_grades_count,
            average_rating=final_average_rating
        )

        return TranscriptResponse(courses=course_results, statistics=statistics)