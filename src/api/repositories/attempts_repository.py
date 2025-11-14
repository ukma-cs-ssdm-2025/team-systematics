from sqlalchemy.orm import Session, load_only, joinedload, defer, selectinload
from sqlalchemy import func
from uuid import UUID
import json
from datetime import datetime, timedelta, timezone
from src.api.services.statistics_service import StatisticsService
from src.utils.datetime_utils import to_utc_iso
from typing import Optional, Dict, Any, List

from src.models.exams import Exam, Question, Option
from src.models.attempts import Attempt, AttemptStatus, Answer, AnswerOption
from src.models.matching_options import MatchingOption
from src.api.schemas.attempts import AnswerUpsert

class AttemptsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_attempt(self, exam_id: UUID, user_id: UUID, duration_minutes: int) -> Attempt:
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise ValueError(f"Invalid duration_minutes: {duration_minutes}")
            
        started_at = datetime.now(timezone.utc)
        due_at = started_at + timedelta(minutes=duration_minutes)
        new_attempt = Attempt(
            exam_id=exam_id,
            user_id=user_id,
            status="in_progress",
            started_at=started_at,
            due_at=due_at,
        ) 
        self.db.add(new_attempt)
        self.db.commit()
        self.db.refresh(new_attempt)
        return new_attempt

    def get_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        return self.db.query(Attempt).filter(Attempt.id == attempt_id).first()

    def upsert_answer(self, attempt_id: UUID, payload: AnswerUpsert) -> Answer:
        question = self.db.query(Question).filter(Question.id == payload.question_id).first()
        if not question:
            raise ValueError("Question not found")

        answer = self.db.query(Answer).options(
            joinedload(Answer.selected_options)
        ).filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == payload.question_id,
        ).first()

        current_time = datetime.now(timezone.utc)

        if not answer:
            answer = Answer(
                attempt_id=attempt_id,
                question_id=payload.question_id,
                saved_at=current_time, 
            )
            self.db.add(answer)
            self.db.flush()
        else:
            answer.saved_at = current_time

        answer.saved_at = current_time

        q_type = str(question.question_type.value)

        if q_type in ('single_choice', 'multi_choice'):
            self.db.query(AnswerOption).filter(
                AnswerOption.answer_id == answer.id
            ).delete(synchronize_session=False)

            if payload.selected_option_ids:
                for option_id in payload.selected_option_ids:
                    new_answer_option = AnswerOption(
                        answer_id=answer.id,
                        selected_option_id=option_id
                    )
                    self.db.add(new_answer_option)
            
            answer.answer_text = None
            answer.answer_json = None

        elif q_type in ('short_answer', 'long_answer'):
            answer.answer_text = payload.text
            answer.answer_json = None

        elif q_type == 'matching':
            answer.answer_text = None
        try:
            if payload.text:
                answer.answer_json = json.loads(payload.text)
            else:
                answer.answer_json = None
        except (json.JSONDecodeError, TypeError):
            answer.answer_json = None

        self.db.commit()
        self.db.refresh(answer)
        
        # Перезавантажуємо answer з selected_options після commit
        answer = self.db.query(Answer).options(
            joinedload(Answer.selected_options)
        ).filter(Answer.id == answer.id).first()
        
        return answer

    def submit_attempt(self, attempt_id: UUID) -> Optional[Attempt]:
        attempt = self.get_attempt(attempt_id)
        if not attempt:
            return None

        current_time = datetime.now(timezone.utc)
        attempt.submitted_at = current_time
        attempt.status = AttemptStatus.submitted
    
        if attempt.started_at:
            time_difference = current_time - attempt.started_at
            attempt.time_spent_seconds = int(time_difference.total_seconds())
            
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
    
    def extend_attempt_time(self, attempt_id: UUID, extra_minutes: int) -> Optional[Attempt]:
        """
        Подовжує дедлайн (due_at) для спроби іспиту на вказану кількість хвилин.

        Args:
            attempt_id: ID спроби, яку потрібно подовжити.
            extra_minutes: Кількість додаткових хвилин (> 0).

        Returns:
            Оновлений об'єкт Attempt або None, якщо спробу не знайдено.
        """
        if extra_minutes <= 0:
            raise ValueError("extra_minutes must be positive")

        attempt = self.get_attempt(attempt_id)
        if not attempt:
            return None

        if not attempt.due_at:
            # Якщо з якоїсь причини due_at немає, просто не змінюємо нічого
            return attempt

        # Подовжуємо дедлайн
        attempt.due_at = attempt.due_at + timedelta(minutes=extra_minutes)

        self.db.commit()
        self.db.refresh(attempt)
        return attempt    

    def _get_question_type(self, q: Question) -> str:
        return q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type)

    def _load_options_by_question(self, question_ids: List[UUID]) -> Dict[UUID, List[Dict[str, Any]]]:
        opts_by_q: Dict[UUID, List[Dict[str, Any]]] = {}
        if not question_ids:
            return opts_by_q
        options = self.db.query(Option).filter(Option.question_id.in_(question_ids)).all()
        for o in options:
            opts_by_q.setdefault(o.question_id, []).append({'id': str(o.id), 'text': o.text})
        return opts_by_q

    def _load_matching_by_question(self, question_ids: List[UUID]) -> Dict[UUID, Dict[str, List[Dict[str, Any]]]]:
        match_by_q: Dict[UUID, Dict[str, List[Dict[str, Any]]]] = {}
        if not question_ids:
            return match_by_q
        matching_rows = self.db.query(MatchingOption).filter(MatchingOption.question_id.in_(question_ids)).all()
        for m in matching_rows:
            q_id = m.question_id
            if q_id not in match_by_q:
                match_by_q[q_id] = {'prompts': [], 'matches': []}
            match_by_q[q_id]['prompts'].append({'id': str(m.id), 'text': m.prompt})
            match_by_q[q_id]['matches'].append({'id': str(m.id), 'text': m.correct_match})
        return match_by_q

    def _format_question(self, q: Question, opts_by_q: Dict[UUID, List[Dict[str, Any]]], match_by_q: Dict[UUID, Dict[str, List[Dict[str, Any]]]]) -> Dict[str, Any]:
        q_type = self._get_question_type(q)
        q_out: Dict[str, Any] = {
            'id': str(q.id),
            'position': q.position,
            'question_type': q_type,
            'title': q.title,
            'points': q.points,
        }
        if q_type in ('single_choice', 'multi_choice'):
            q_out['options'] = opts_by_q.get(q.id, [])
        elif q_type == 'short_answer':
            q_out['input_type'] = 'text'
        elif q_type == 'matching':
            q_out['matching_data'] = match_by_q.get(q.id, {'prompts': [], 'matches': []})
        return q_out

    def get_attempt_with_details(self, attempt_id: UUID) -> Optional[Dict[str, Any]]:
        """Збирає та форматує всю інформацію для сторінки складання іспиту.

        Цей метод агрегує дані про спробу, іспит, відсортовані питання,
        варіанти відповідей, дані для питань на відповідність та збережені
        відповіді користувача в один зручний для фронтенду об'єкт.
        """
        attempt = self.get_attempt(attempt_id)
        if not attempt or not attempt.exam:
            return None
        exam = attempt.exam

        # 1. Завантажуємо питання, впорядковані за позицією
        questions: List[Question] = (
            self.db.query(Question)
            .filter(Question.exam_id == exam.id)
            .order_by(Question.position)
            .all()
        )
        question_ids = [q.id for q in questions]

        # 2. Оптимізація: завантажуємо всі опції та дані для 'matching' одним запитом
        opts_by_q = self._load_options_by_question(question_ids)
        match_by_q = self._load_matching_by_question(question_ids)

        # 3. Формуємо фінальний список питань для фронтенду
        questions_out = [self._format_question(q, opts_by_q, match_by_q) for q in questions]

        # 4. Збираємо все в один об'єкт-результат
        result: Dict[str, Any] = {
            'attempt_id': str(attempt.id),
            'exam_id': str(exam.id),
            'exam_title': exam.title,
            'duration_minutes': exam.duration_minutes,
            'status': str(attempt.status.value) if hasattr(attempt.status, 'value') else str(attempt.status),
            'started_at': to_utc_iso(attempt.started_at),
            'due_at': to_utc_iso(attempt.due_at),
            'questions': questions_out,
        }
        return result

    # Note: previous implementation was refactored above; duplicate removed.

    def get_attempt_result_raw(self, attempt_id: UUID) -> Optional[Dict[str, Any]]:
        attempt = self.db.query(Attempt).options(
            joinedload(Attempt.exam),
            selectinload(Attempt.answers)  # Завантажуємо answers для підрахунку
        ).filter(Attempt.id == attempt_id).first()
        if not attempt:
            return None

        # Рахуємо реальну кількість відповідей з таблиці answers
        # а не з полів correct_answers + incorrect_answers + pending_count
        actual_answers_count = len(attempt.answers) if attempt.answers else 0

        return {
            "exam_title": attempt.exam.title,
            "attempt_status": attempt.status.value,
            "score": attempt.earned_points or 0,
            "time_spent_seconds": attempt.time_spent_seconds or 0,
            "total_questions": len(attempt.exam.questions),
            "answers_given": actual_answers_count,  # Використовуємо реальну кількість відповідей
            "correct_answers": attempt.correct_answers or 0,
            "incorrect_answers": attempt.incorrect_answers or 0,
            "pending_count": attempt.pending_count or 0,
        }

    def get_user_attempt_count(self, user_id: UUID, exam_id: UUID) -> int:
        """
        Рахує кількість існуючих спроб для конкретного користувача та іспиту.
        """
        count = self.db.query(Attempt).filter(
            Attempt.exam_id == exam_id,
            Attempt.user_id == user_id
        ).count()
        return count

    def get_attempt_for_review(self, attempt_id: UUID) -> Optional[Attempt]:
        """
        Завантажує спробу з усіма необхідними пов'язаними даними для
        побудови сторінки детального огляду (review).
        Оцінки розраховуються нальоту, тому не завантажуємо earned_points з БД.
        Використовуємо load_only для Answer, щоб завантажити тільки потрібні стовпчики.
        """
        return self.db.query(Attempt).options(
            joinedload(Attempt.exam).joinedload(Exam.questions).joinedload(Question.options),
            joinedload(Attempt.exam).joinedload(Exam.questions).joinedload(Question.matching_options),
            selectinload(Attempt.answers),
            selectinload(Attempt.answers).selectinload(Answer.selected_options)
        ).filter(Attempt.id == attempt_id).first()

    def update_answer_score(self, attempt_id: UUID, answer_id: UUID, earned_points: float) -> Optional[Answer]:
        """
        Оновлює оцінку для конкретної відповіді.
        """
        answer = self.db.query(Answer).filter(
            Answer.id == answer_id,
            Answer.attempt_id == attempt_id
        ).first()
        
        if not answer:
            return None
        
        answer.earned_points = earned_points
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def get_attempts_statistics_for_exam(self, exam_id: UUID) -> dict:
        """Отримує статистику для спроб на іспиті"""
        attempts = self.db.query(Attempt).filter(Attempt.exam_id == exam_id).all()
        
        scores = [attempt.score_percent for attempt in attempts if attempt.score_percent is not None]
        
        return StatisticsService.calculate_statistics(scores)
