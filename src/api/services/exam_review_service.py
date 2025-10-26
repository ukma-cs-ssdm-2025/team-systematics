from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from src.models.attempts import Attempt, Answer
from src.models.exams import Exam, Question, Option, MatchingOption, QuestionType
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.api.errors.app_errors import NotFoundError

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

    def get_attempt_review(self, attempt_id: UUID, db: Session) -> dict:
        """
        Готує дані для огляду спроби з коректним розрахунком балів,
        масштабованих до 100-бальної системи.
        """
        attempts_repo = AttemptsRepository(db)
        weights_repo = WeightsRepository(db)
        
        # 1. Отримуємо дані про спробу та ваги
        attempt = attempts_repo.get_attempt_for_review(attempt_id)
        if not attempt:
            raise NotFoundError(f"Спроба з ID {attempt_id} не знайдена.")
        
        weights_map = weights_repo.get_all_weights()
    
        # 2. Розраховуємо загальну вагу іспиту
        total_exam_weight = 0
        for question in attempt.exam.questions:
            # Використовуємо вагу з мапи, або 1 за замовчуванням
            total_exam_weight += weights_map.get(question.question_type, 1)

        # 3. Розраховуємо вартість однієї одиниці ваги
        # (уникаємо ділення на нуль, якщо в іспиті немає питань)
        if total_exam_weight == 0:
            points_per_weight_unit = 0.0
        else:
            # Масштабуємо до 100 балів
            points_per_weight_unit = 100.0 / total_exam_weight

        # 4. Створюємо мапу реальних балів для кожного питання
        true_points_map = {}
        for question in attempt.exam.questions:
            weight = weights_map.get(question.question_type, 1)
            true_points_map[question.id] = weight * points_per_weight_unit
        
        student_answers_map = {answer.question_id: answer for answer in attempt.answers}
        
        review_questions = []
        for question in sorted(attempt.exam.questions, key=lambda q: q.position):
            student_answer = student_answers_map.get(question.id)
            # 5. Передаємо розраховані бали в допоміжну функцію
            true_question_points = true_points_map.get(question.id, 0.0)
            question_data = self._build_question_review_data(question, student_answer, true_question_points)
            review_questions.append(question_data)
            
        return ExamAttemptReviewResponse(
            exam_title=attempt.exam.title,
            questions=review_questions
        ).model_dump()

    def _build_question_review_data(
            self,
            question: Question,
            student_answer: Answer | None,
            true_question_points: float
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
            return self._build_single_choice_data(base_data, question, student_answer)
        
        elif q_type == QuestionType.multi_choice:
            return self._build_multi_choice_data(base_data, question, student_answer)
            
        elif q_type == QuestionType.long_answer:
            return self._build_long_answer_data(base_data, student_answer)
            
        elif q_type == QuestionType.short_answer:
            return self._build_short_answer_data(base_data, question, student_answer)
            
        elif q_type == QuestionType.matching:
            return self._build_matching_data(base_data, question, student_answer)
            
        return base_data

    # --- Функції-конструктори для кожного типу питання ---

    def _build_single_choice_data(self, base_data, question, student_answer):
        options_data = []
        earned_points = 0
        
        selected_option_id = (student_answer.selected_options[0].selected_option_id
            if student_answer and student_answer.selected_options else None)

        for opt in question.options:
            is_selected = (opt.id == selected_option_id)
            options_data.append(SingleChoiceOption(
                id=str(opt.id),
                text=opt.text,
                is_correct=opt.is_correct,
                is_selected=is_selected
            ))
            if is_selected and opt.is_correct:
                earned_points = base_data["points"]

        return SingleChoiceQuestionReview(
            **base_data,
            options=options_data,
            earned_points=earned_points
        )

    def _build_multi_choice_data(self, base_data, question, student_answer):
        options_data = []
        total_earned_points = 0
        correct_option_ids = {opt.id for opt in question.options if opt.is_correct}
        
        # Розрахунок балів за кожну правильну опцію (може бути інша логіка) 
        points_per_correct_option = (base_data["points"] / len(correct_option_ids)) if correct_option_ids else 0
        
        selected_option_ids = {so.selected_option_id for so in student_answer.selected_options} if student_answer else set()

        for opt in question.options:
            is_selected = opt.id in selected_option_ids
            earned_points_per_option = 0
            if is_selected:
                if opt.is_correct:
                    earned_points_per_option = points_per_correct_option
                    total_earned_points += points_per_correct_option

            options_data.append(MultiChoiceOption(
                id=str(opt.id),
                text=opt.text,
                is_correct=opt.is_correct,
                is_selected=is_selected,
                earned_points_per_option=round(earned_points_per_option)
            ))
            
        return MultiChoiceQuestionReview(
            **base_data,
            options=options_data,
            earned_points=round(total_earned_points)
        )

    def _build_long_answer_data(self, base_data, student_answer):
        return LongAnswerQuestionReview(
            **base_data,
            # 'earned_points' для цього типу завжди null до ручної перевірки
            earned_points=None, 
            student_answer_text=student_answer.answer_text if student_answer else ""
        )
        
    def _build_short_answer_data(self, base_data, question, student_answer):
        correct_answers = {opt.text.lower() for opt in question.options if opt.is_correct}
        student_ans_text = student_answer.answer_text if student_answer else ""
        earned_points = 0
        
        if student_ans_text.lower() in correct_answers:
            earned_points = base_data["points"]
            
        return ShortAnswerQuestionReview(
            **base_data,
            student_answer_text=student_ans_text,
            correct_answer_text=next(iter(correct_answers), None), # Показуємо один з можливих правильних варіантів
            earned_points=earned_points
        )
        
    def _build_matching_data(self, base_data, question, student_answer):
        prompts_data = []
        total_earned_points = 0
        
        # Створюємо унікальні ID для `matches` з тексту, оскільки в БД їх немає
        all_matches = sorted(list({opt.correct_match for opt in question.matching_options}))
        matches_data = [MatchingMatch(id=match_text, text=match_text) for match_text in all_matches]
        
        points_per_match = (base_data["points"] / len(question.matching_options)) if question.matching_options else 0
        
        student_pairs = student_answer.answer_json if student_answer and student_answer.answer_json else {}

        for pair in question.matching_options:
            student_match = student_pairs.get(pair.prompt)
            earned_points_per_match = 0
            if student_match == pair.correct_match:
                earned_points_per_match = points_per_match
                total_earned_points += earned_points_per_match

            prompts_data.append(MatchingPrompt(
                id=str(pair.id), # Використовуємо ID з MatchingOption
                text=pair.prompt,
                student_match_id=student_match,
                correct_match_id=pair.correct_match,
                earned_points_per_match=round(earned_points_per_match)
            ))
            
        return MatchingQuestionReview(
            **base_data,
            matching_data=MatchingData(prompts=prompts_data, matches=matches_data),
            earned_points=round(total_earned_points)
        )