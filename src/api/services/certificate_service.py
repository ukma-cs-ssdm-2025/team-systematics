from uuid import UUID
from sqlalchemy.orm import Session
from collections import defaultdict
from src.api.repositories.certificate_repository import CertificateRepository
from src.api.schemas.certificate import CertificateResponse, CourseResult, Statistics

class CertificateService:
    def _convert_rating_to_grades(self, rating: float) -> tuple[str, str]:
        """
        Конвертує 100-бальний рейтинг в оцінки ECTS та національну
        на основі наданої таблиці.
        """
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

    def get_certificate_for_user(self, user_id: UUID, db: Session) -> CertificateResponse:
        """
        Головний метод, що збирає, обробляє та форматує дані для атестату.
        """
        repository = CertificateRepository(db)
        
        # 1. Отримуємо всі необхідні дані з БД
        all_exams = repository.get_all_exams()
        user_attempts = repository.get_all_attempts_by_user(user_id)

        # 2. Знаходимо найкращий результат (рейтинг) для кожного іспиту
        max_scores = defaultdict(float)
        for attempt in user_attempts:
            # Перевіряємо, що оцінка існує
            if attempt.earned_points is not None:
                current_max = max_scores[attempt.exam_id]
                max_scores[attempt.exam_id] = max(current_max, attempt.earned_points)

        # 3. Формуємо список курсів та одночасно збираємо статистику
        course_results: list[CourseResult] = []
        completed_courses_count = 0
        a_grades_count = 0
        total_rating_sum = 0.0

        for exam in all_exams:
            # Перевіряємо, чи є у студента хоча б одна спроба для цього іспиту
            if exam.id in max_scores:
                rating = max_scores[exam.id]
                ects_grade, national_grade = self._convert_rating_to_grades(rating)
                pass_status = "Так" if rating >= exam.pass_threshold else "Ні"
                
                course_results.append(CourseResult(
                    id=exam.id,
                    course_name=exam.title,
                    rating=round(rating, 2),
                    ects_grade=ects_grade,
                    national_grade=national_grade,
                    pass_status=pass_status
                ))
                
                # Оновлюємо лічильники для статистики
                completed_courses_count += 1
                total_rating_sum += rating
                if ects_grade == "A":
                    a_grades_count += 1
            else:
                # Якщо спроб не було, додаємо курс з порожніми полями
                course_results.append(CourseResult(
                    id=exam.id,
                    course_name=exam.title,
                    rating=None, ects_grade=None, national_grade=None, pass_status=None
                ))

        # 4. Розраховуємо середній рейтинг, уникаючи ділення на нуль
        average_rating = (total_rating_sum / completed_courses_count) if completed_courses_count > 0 else 0.0
        
        statistics = Statistics(
            completed_courses=completed_courses_count,
            total_courses=len(all_exams),
            a_grades_count=a_grades_count,
            average_rating=round(average_rating, 2)
        )

        # 5. Збираємо фінальну відповідь
        return CertificateResponse(courses=course_results, statistics=statistics)