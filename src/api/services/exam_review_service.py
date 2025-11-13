from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from src.models.attempts import Attempt, Answer
from src.models.exams import Exam, Question, Option, MatchingOption, QuestionType
from src.models.users import User
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.api.repositories.flagged_answers_repository import FlaggedAnswersRepository
from src.api.errors.app_errors import NotFoundError
from src.utils.largest_remainder import distribute_largest_remainder

# Імпортуємо схеми Pydantic для відповіді
from src.api.schemas.exam_review import (
    ExamAttemptReviewResponse,
    SingleChoiceQuestionReview,
    MultiChoiceQuestionReview,
    LongAnswerQuestionReview,
    ShortAnswerQuestionReview,
    MatchingQuestionReview,
    SingleChoiceOption,
    MultiChoiceOption,
    MatchingData,
    MatchingPrompt,
    MatchingMatch
)

class ExamReviewService:
    # Конструктор не потрібен, сервіс залишається stateless

    def get_attempt_review(self, attempt_id: UUID, db: Session, current_user: User = None) -> dict:
        """
        Готує дані для огляду спроби з коректним розрахунком балів,
        масштабованих до 100-бальної системи.
        
        Якщо студент ще не використав всі спроби, правильні відповіді будуть приховані.
        """
        attempts_repo = AttemptsRepository(db)
        weights_repo = WeightsRepository(db)
        
        # 1. Отримуємо дані про спробу та ваги
        attempt = attempts_repo.get_attempt_for_review(attempt_id)
        if not attempt:
            raise NotFoundError(f"Спроба з ID {attempt_id} не знайдена.")
        
        # 2. Перевіряємо, чи студент використав всі спроби (для студентів)
        # Для вчителів завжди показуємо правильні відповіді
        show_correct_answers = True
        if current_user and hasattr(current_user, 'role'):
            # Перевіряємо, чи користувач - студент (не вчитель/наглядач)
            user_role = str(current_user.role).lower().strip() if current_user.role else None
            if user_role == 'student' and attempt.user_id == current_user.id:
                # Перевіряємо, чи студент використав всі спроби
                user_attempt_count = attempts_repo.get_user_attempt_count(current_user.id, attempt.exam_id)
                if user_attempt_count < attempt.exam.max_attempts:
                    show_correct_answers = False
        
        weights_map = weights_repo.get_all_weights()
    
        total_exam_weight = sum(
            weights_map.get(q.question_type, 1) for q in attempt.exam.questions
        )

        if total_exam_weight == 0:
            points_per_weight_unit = 0.0
        else:
            points_per_weight_unit = 100.0 / total_exam_weight

        # 1. Розраховуємо точні (float) бали для кожного питання
        true_points_map = {
            q.id: weights_map.get(q.question_type, 1) * points_per_weight_unit
            for q in attempt.exam.questions
        }
        
        # 2. Викликаємо функцію розподілу залишку, щоб отримати гарантовану суму 100
        final_points_map = distribute_largest_remainder(true_points_map, target_total=100)
        
        # 3. Подальша логіка використовує вже скориговані цілі бали
        student_answers_map = {answer.question_id: answer for answer in attempt.answers}
        
        review_questions = []
        for question in sorted(attempt.exam.questions, key=lambda q: q.position):
            student_answer = student_answers_map.get(question.id)
            final_question_points = final_points_map.get(question.id, 0)
            
            question_data = self._build_question_review_data(
                question, 
                student_answer, 
                final_question_points,
                db,
                show_correct_answers
            )
            review_questions.append(question_data)
            
        return ExamAttemptReviewResponse(
            exam_id=str(attempt.exam.id),  # Додаємо exam_id для навігації
            exam_title=attempt.exam.title,
            show_correct_answers=show_correct_answers,
            questions=review_questions
        ).model_dump()

    def _build_question_review_data(
            self,
            question: Question,
            student_answer: Answer | None,
            true_question_points: float,
            db: Session,
            show_correct_answers: bool = True
        ) -> dict:
        """Допоміжна функція для побудови структури одного питання."""
        
        base_data = {
            "id": str(question.id),
            "position": question.position,
            "title": question.title,
            "points": true_question_points,
            "question_type": question.question_type.value
        }

        # Логіка для кожного типу питання
        q_type = question.question_type

        if q_type == QuestionType.single_choice:
            return self._build_single_choice_data(base_data, question, student_answer, show_correct_answers)
        
        elif q_type == QuestionType.multi_choice:
            return self._build_multi_choice_data(base_data, question, student_answer, show_correct_answers)
            
        elif q_type == QuestionType.long_answer:
            return self._build_long_answer_data(base_data, student_answer, db)
            
        elif q_type == QuestionType.short_answer:
            return self._build_short_answer_data(base_data, question, student_answer, show_correct_answers)
            
        elif q_type == QuestionType.matching:
            return self._build_matching_data(base_data, question, student_answer, show_correct_answers)
            
        return base_data

    # --- Функції-конструктори для кожного типу питання ---

    def _build_single_choice_data(self, base_data, question, student_answer, show_correct_answers=True):
        options_data = []
        earned_points = 0
        
        selected_option_id = (student_answer.selected_options[0].selected_option_id
            if student_answer and student_answer.selected_options else None)

        for opt in question.options:
            is_selected = (opt.id == selected_option_id)
            # Приховуємо правильність відповіді, якщо не дозволено показувати правильні відповіді
            is_correct = opt.is_correct if show_correct_answers else False
            options_data.append(SingleChoiceOption(
                id=str(opt.id),
                text=opt.text,
                is_correct=is_correct,
                is_selected=is_selected
            ))
            if is_selected and opt.is_correct:
                earned_points = base_data["points"]

        return SingleChoiceQuestionReview(
            **base_data,
            options=options_data,
            earned_points=earned_points if show_correct_answers else None  # Приховуємо бали, якщо не показуємо правильні відповіді
        )

    def _build_multi_choice_data(self, base_data, question, student_answer, show_correct_answers=True):
        options_data = []
        total_earned_points = 0
        correct_option_ids = {opt.id for opt in question.options if opt.is_correct}
        
        # Розрахунок балів за кожну правильну опцію (може бути інша логіка) 
        points_per_correct_option = (base_data["points"] / len(correct_option_ids)) if correct_option_ids else 0
        
        selected_option_ids = {so.selected_option_id for so in student_answer.selected_options} if student_answer else set()

        for opt in question.options:
            is_selected = opt.id in selected_option_ids
            earned_points_per_option = 0
            if is_selected and opt.is_correct:
                    earned_points_per_option = points_per_correct_option
                    total_earned_points += points_per_correct_option

            # Приховуємо правильність відповіді, якщо не дозволено показувати правильні відповіді
            is_correct = opt.is_correct if show_correct_answers else False
            options_data.append(MultiChoiceOption(
                id=str(opt.id),
                text=opt.text,
                is_correct=is_correct,
                is_selected=is_selected,
                earned_points_per_option=earned_points_per_option if show_correct_answers else 0
            ))
            
        return MultiChoiceQuestionReview(
            **base_data,
            options=options_data,
            earned_points=total_earned_points if show_correct_answers else None  # Приховуємо бали, якщо не показуємо правильні відповіді
        )

    def _build_long_answer_data(self, base_data, student_answer, db: Session = None):
        # earned_points може бути встановлено вчителем вручну
        # Якщо earned_points встановлено в Answer, використовуємо його
        answer_id = str(student_answer.id) if student_answer else None
        # earned_points зберігається в масштабі final_points (масштабованих до 100 балів)
        earned_points = None
        if student_answer and student_answer.earned_points is not None:
            # earned_points вже в правильному масштабі (final_points)
            earned_points = student_answer.earned_points
        
        # Перевіряємо, чи позначена відповідь для перевірки на плагіат
        is_flagged = False
        if answer_id and db:
            repo = FlaggedAnswersRepository()
            is_flagged = repo.is_flagged(db, UUID(answer_id))
        
        return LongAnswerQuestionReview(
            **base_data,
            earned_points=earned_points, 
            student_answer_text=student_answer.answer_text if student_answer else "",
            answer_id=answer_id,
            is_flagged=is_flagged
        )
        
    def _build_short_answer_data(self, base_data, question, student_answer, show_correct_answers=True):
        correct_answers = {opt.text.lower() for opt in question.options if opt.is_correct}
        student_ans_text = student_answer.answer_text if student_answer else ""
        earned_points = 0
        
        if student_ans_text.lower() in correct_answers:
            earned_points = base_data["points"]
        
        # Приховуємо правильну відповідь, якщо не дозволено показувати правильні відповіді
        correct_answer_text = next(iter(correct_answers), None) if show_correct_answers else None
            
        return ShortAnswerQuestionReview(
            **base_data,
            student_answer_text=student_ans_text,
            correct_answer_text=correct_answer_text,
            earned_points=earned_points if show_correct_answers else None  # Приховуємо бали, якщо не показуємо правильні відповіді
        )
        
    def _build_matching_data(self, base_data, question, student_answer, show_correct_answers=True):
        prompts_data = []
        total_earned_points = 0.0
        
        # 1. Створюємо мапу правильних пар: ID prompt'а -> ID match'а
        correct_pairs_map = {str(opt.id): str(opt.id) for opt in question.matching_options}
        
        # 2. Створюємо список унікальних matches для фронтенду
        matches_data = [
            MatchingMatch(id=str(opt.id), text=opt.correct_match) 
            for opt in question.matching_options
        ]
        
        # 3. Розраховуємо бали за кожну правильну пару
        points_per_match = (base_data["points"] / len(question.matching_options)) if question.matching_options else 0.0
        
        # 4. Отримуємо відповіді студента
        student_pairs = student_answer.answer_json if student_answer and student_answer.answer_json else {}

        # 5. Ітеруємо по всіх можливих prompts
        for pair in question.matching_options:
            prompt_id_str = str(pair.id)
            correct_match_id_str = correct_pairs_map[prompt_id_str]
            student_selected_match_id_str = student_pairs.get(prompt_id_str)
            
            earned_points_per_match = 0.0

            # ПОРІВНЮЄМО ID, а не текст
            if student_selected_match_id_str == correct_match_id_str:
                earned_points_per_match = points_per_match
                total_earned_points += points_per_match

            student_match_text = None
            if student_selected_match_id_str:
                found_match = next((m.text for m in matches_data if m.id == student_selected_match_id_str), None)
                student_match_text = found_match

            # Приховуємо правильну відповідь, якщо не дозволено показувати правильні відповіді
            correct_match_id = pair.correct_match if show_correct_answers else ""
            prompts_data.append(MatchingPrompt(
                id=prompt_id_str,
                text=pair.prompt,
                student_match_id=student_match_text,
                correct_match_id=correct_match_id,
                earned_points_per_match=earned_points_per_match if show_correct_answers else 0.0
            ))
            
        return MatchingQuestionReview(
            **base_data,
            matching_data=MatchingData(prompts=prompts_data, matches=matches_data),
            earned_points=total_earned_points if show_correct_answers else None  # Приховуємо бали, якщо не показуємо правильні відповіді
        )
