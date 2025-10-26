import json
from uuid import UUID
from pathlib import Path
from fastapi import HTTPException, status
from typing import Any

# Припускаємо, що ваш файл лежить у папці 'mocks' у корені проєкту
# Шлях: /team-systematics/mocks/examAttemptReview.json
MOCK_FILE_PATH = Path(__file__).parent.parent.parent / "mocks" / "examAttemptReview.json"

class ExamReviewService:
    def __init__(self):
        # Ми можемо завантажити та кешувати mock-дані при старті
        try:
            with open(MOCK_FILE_PATH, 'r', encoding='utf-8') as f:
                self.mock_data = json.load(f)
        except FileNotFoundError:
            # Це важливо, щоб ви знали, якщо шлях до файлу неправильний
            raise RuntimeError(f"Не вдалося знайти mock-файл: {MOCK_FILE_PATH}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Не вдалося розпарсити JSON: {MOCK_FILE_PATH}")

    def get_attempt_review(self, attempt_id: UUID, db: Any) -> dict:
        """
        Отримує деталізований огляд спроби іспиту.
        
        TODO: Замінити цю mock-логіку на реальні запити до БД
              для збирання даних про спробу, питання та відповіді.
        """
        
        # Наразі ми просто ігноруємо attempt_id та db
        # і повертаємо закешовані дані з файлу.
        if not self.mock_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mock-дані для огляду спроби не знайдено."
            )
            
        # У реальному житті тут буде:
        # 1. Запит до БД, щоб знайти спробу (attempt) за ID
        # 2. Запит до БД, щоб отримати назву іспиту
        # 3. Складний запит, щоб зібрати всі питання,
        #    відповіді студента та правильні відповіді.
        # 4. Форматування даних у потрібну структуру.
        
        return self.mock_data