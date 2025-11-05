from collections import defaultdict
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.models.attempts import Attempt, Answer
from src.models.exams import Exam, Question, QuestionType, QuestionTypeWeight

class GradingResult:
    """Проста структура для повернення результатів оцінювання."""
    def __init__(self):
        self.earned_weight = 0.0
        self.correct_count = 0
        self.incorrect_count = 0
        self.pending_count = 0
        self.total_answers_given = 0

class GradingService:
    def _ensure_question_points_are_set(self, db: Session, exam: Exam) -> None:
        questions_to_update = [q for q in exam.questions if q.points is None]
        if not questions_to_update:
            return
        weights = {w.question_type: w.weight for w in db.query(QuestionTypeWeight).all()}
        for q in questions_to_update:
            q.points = weights.get(q.question_type, 1)  # 1 — вага за замовчуванням
        db.flush()

    def _build_correct_data(self, exam: Exam) -> Dict[Any, Dict[str, Any]]:
        data: Dict[Any, Dict[str, Any]] = defaultdict(dict)
        for q in exam.questions:
            qt = q.question_type
            if qt in (QuestionType.single_choice, QuestionType.multi_choice):
                data[q.id]["options"] = {opt.id for opt in q.options if getattr(opt, "is_correct", False)}
            elif qt == QuestionType.short_answer:
                data[q.id]["texts"] = {opt.text.lower() for opt in q.options if getattr(opt, "is_correct", False)}
            elif qt == QuestionType.matching:
                data[q.id]["pairs"] = {str(p.id): str(p.id) for p in q.matching_options}
        return data

    @staticmethod
    def _points(q: Question) -> float:
        return float(q.points or 0.0)

    def _grade_long_answer(self, result: GradingResult, *_):
        """
        Довга відповідь оцінюється вручну: відмічаємо як pending.
        """
        result.pending_count += 1
        return 0.0, None  # потребує ручної перевірки

    def _grade_single_choice(self, q: Question, a: Answer, correct: Dict[str, Any]) -> Tuple[float, bool]:
        user_ids = {opt.selected_option_id for opt in a.selected_options}
        return (self._points(q), True) if user_ids == correct.get("options", set()) else (0.0, False)

    def _grade_short_answer(self, q: Question, a: Answer, correct: Dict[str, Any]) -> Tuple[float, bool]:
        user_text = (a.answer_text or "").lower()
        return (self._points(q), True) if user_text in correct.get("texts", set()) else (0.0, False)

    def _grade_multi_choice(self, q: Question, a: Answer, correct: Dict[str, Any]) -> Tuple[float, bool]:
        user_ids = {o.selected_option_id for o in a.selected_options}
        correct_ids = correct.get("options", set())
        if not correct_ids:
            return 0.0, False
        per_opt = self._points(q) / len(correct_ids)
        earned = sum(per_opt for oid in user_ids if oid in correct_ids)
        is_full = (user_ids == correct_ids)  # повністю правильним — лише при 100% збігу
        return earned, is_full

    def _grade_matching(self, q: Question, a: Answer, correct: Dict[str, Any]) -> Tuple[float, bool]:
        user_pairs = a.answer_json or {}
        correct_map = correct.get("pairs", {})
        if not correct_map:
            return 0.0, False
        per_match = self._points(q) / len(correct_map)
        earned = sum(per_match for k, v in correct_map.items() if user_pairs.get(k) == v)
        is_full = (user_pairs == correct_map)
        return earned, is_full

    def calculate_score(self, db: Session, attempt: Attempt) -> GradingResult:
        self._ensure_question_points_are_set(db, attempt.exam)

        result = GradingResult()
        result.total_answers_given = len(attempt.answers)
        correct_data = self._build_correct_data(attempt.exam)

        handlers = {
            QuestionType.long_answer:   lambda q, a: self._grade_long_answer(result, q, a),
            QuestionType.single_choice: lambda q, a: self._grade_single_choice(q, a, correct_data[q.id]),
            QuestionType.short_answer:  lambda q, a: self._grade_short_answer(q, a, correct_data[q.id]),
            QuestionType.multi_choice:  lambda q, a: self._grade_multi_choice(q, a, correct_data[q.id]),
            QuestionType.matching:      lambda q, a: self._grade_matching(q, a, correct_data[q.id]),
        }

        for ans in attempt.answers:
            q = ans.question
            handler = handlers.get(q.question_type)
            if handler is None:
                result.incorrect_count += 1
                continue

            earned, is_correct = handler(q, ans)

            if is_correct is None:
                continue

            result.earned_weight += earned
            if is_correct:
                result.correct_count += 1
            else:
                result.incorrect_count += 1

        return result