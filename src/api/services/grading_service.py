from sqlalchemy.orm import Session
from collections import defaultdict
from src.models.attempts import Attempt
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
    def _ensure_question_points_are_set(self, db: Session, exam: Exam):
        """
        Перевіряє і заповнює бали для питань в іспиті, якщо їх немає,
        для статично створених питань у базі даних.
        """
        questions_to_update = [q for q in exam.questions if q.points is None]
        if not questions_to_update:
            return

        weights_map = {w.question_type: w.weight for w in db.query(QuestionTypeWeight).all()}

        for question in questions_to_update:
            weight = weights_map.get(question.question_type, 1) # 1 - вага за замовчуванням
            question.points = weight
        
        db.flush()

    def calculate_score(self, db: Session, attempt: Attempt) -> GradingResult:
        """
        Обчислює результати для спроби, не змінюючи її в базі даних.
        Повертає об'єкт GradingResult зі всією статистикою.
        """
        self._ensure_question_points_are_set(db, attempt.exam)

        result = GradingResult()
        result.total_answers_given = len(attempt.answers)
        
        # зручно зберігаємо усі правильні відповді
        correct_data_map = defaultdict(dict)
        for question in attempt.exam.questions:
            q_type = question.question_type
            if q_type in (QuestionType.single_choice, QuestionType.multi_choice):
                correct_data_map[question.id]['options'] = {opt.id for opt in question.options if opt.is_correct}
            elif q_type == QuestionType.short_answer:
                correct_data_map[question.id]['texts'] = {opt.text.lower() for opt in question.options if opt.is_correct}
            elif q_type == QuestionType.matching:
                correct_data_map[question.id]['pairs'] = {p.prompt: p.correct_match for p in question.matching_options}
        
        for answer in attempt.answers:
            question = answer.question
            is_correct = False

            if question.question_type == QuestionType.long_answer:
                result.pending_count += 1
                continue # Пропускаємо оцінювання

            correct_data = correct_data_map[question.id]
            
            if question.question_type in (QuestionType.single_choice, QuestionType.multi_choice):
                user_option_ids = {ans_opt.selected_option_id for ans_opt in answer.options}
                if user_option_ids == correct_data.get('options', set()):
                    is_correct = True
            
            elif question.question_type == QuestionType.short_answer:
                user_text = (answer.answer_text or "").lower()
                if user_text in correct_data.get('texts', set()):
                    is_correct = True
            
            elif question.question_type == QuestionType.matching:
                user_pairs = answer.answer_json or {}
                if user_pairs == correct_data.get('pairs', {}):
                    is_correct = True

            if is_correct:
                result.correct_count += 1
                result.earned_weight += float(question.points or 0.0)
            else:
                result.incorrect_count += 1

        return result