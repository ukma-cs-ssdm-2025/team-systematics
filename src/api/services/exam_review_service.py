from uuid import UUID
from sqlalchemy.orm import Session
from src.models.attempts import Answer
from src.models.exams import Question, QuestionType
from src.models.users import User
from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.repositories.weights_repository import WeightsRepository
from src.api.repositories.flagged_answers_repository import FlaggedAnswersRepository
from src.api.repositories.plagiarism_repository import PlagiarismRepository
from src.api.errors.app_errors import NotFoundError
from src.utils.largest_remainder import distribute_largest_remainder
from src.api.services.grading_service import GradingService

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
        
        plagiarism_matches = self._get_plagiarism_matches(db, attempt_id)
        show_correct_answers = self._should_show_correct_answers(
            current_user, attempt, attempts_repo
        )
        
        weights_map = weights_repo.get_all_weights()
        final_points_map = self._calculate_final_points_map(attempt, weights_map)
        student_answers_map = {answer.question_id: answer for answer in attempt.answers}
        question_text_offsets = self._build_question_text_offsets(
            attempt.exam.questions, student_answers_map
        )
        
        review_questions = self._build_review_questions(
            attempt.exam.questions,
            student_answers_map,
            final_points_map,
            db,
            show_correct_answers,
            plagiarism_matches,
            question_text_offsets
        )
            
        return ExamAttemptReviewResponse(
            exam_id=str(attempt.exam.id),  # Додаємо exam_id для навігації
            exam_title=attempt.exam.title,
            show_correct_answers=show_correct_answers,
            questions=review_questions
        ).model_dump()
    
    @staticmethod
    def _get_plagiarism_matches(db: Session, attempt_id: UUID) -> list:
        """Отримує інформацію про плагіат для спроби."""
        plagiarism_repo = PlagiarismRepository()
        plagiarism_check = plagiarism_repo.get_by_attempt_id(db, attempt_id)
        if plagiarism_check and plagiarism_check.details:
            return plagiarism_check.details.get("matches", [])
        return []
    
    @staticmethod
    def _should_show_correct_answers(
        current_user: User, attempt, attempts_repo
    ) -> bool:
        """Визначає, чи потрібно показувати правильні відповіді."""
        if not current_user or not hasattr(current_user, 'role'):
            return True
        
        user_role = str(current_user.role).lower().strip() if current_user.role else None
        if user_role != 'student' or attempt.user_id != current_user.id:
            return True
        
        user_attempt_count = attempts_repo.get_user_attempt_count(
            current_user.id, attempt.exam_id
        )
        return user_attempt_count >= attempt.exam.max_attempts
    
    @staticmethod
    def _calculate_final_points_map(attempt, weights_map: dict) -> dict:
        """Розраховує фінальні бали для кожного питання."""
        total_exam_weight = sum(
            weights_map.get(q.question_type, 1) for q in attempt.exam.questions
        )
        
        if total_exam_weight == 0:
            points_per_weight_unit = 0.0
        else:
            points_per_weight_unit = 100.0 / total_exam_weight
        
        true_points_map = {
            q.id: weights_map.get(q.question_type, 1) * points_per_weight_unit
            for q in attempt.exam.questions
        }
        
        return distribute_largest_remainder(true_points_map, target_total=100)
    
    @staticmethod
    def _build_question_text_offsets(questions, student_answers_map: dict) -> dict:
        """Будує мапу для перерахунку ranges з об'єднаного тексту на окремі питання."""
        long_answer_questions = sorted(
            [q for q in questions if q.question_type == QuestionType.long_answer],
            key=lambda q: q.position
        )
        question_text_offsets = {}
        current_offset = 0
        separator = "\n\n"
        separator_len = len(separator)
        
        for idx, q in enumerate(long_answer_questions):
            answer = student_answers_map.get(q.id)
            answer_text = answer.answer_text if answer and answer.answer_text else ""
            if answer_text:
                question_start = current_offset
                question_end = current_offset + len(answer_text)
                question_text_offsets[q.id] = (question_start, question_end)
                current_offset = question_end
                if idx < len(long_answer_questions) - 1:
                    current_offset += separator_len
        
        return question_text_offsets
    
    def _build_review_questions(
        self,
        questions,
        student_answers_map: dict,
        final_points_map: dict,
        db: Session,
        show_correct_answers: bool,
        plagiarism_matches: list,
        question_text_offsets: dict
    ) -> list:
        """Будує список питань для перегляду."""
        review_questions = []
        for question in sorted(questions, key=lambda q: q.position):
            student_answer = student_answers_map.get(question.id)
            final_question_points = final_points_map.get(question.id, 0)
            
            plagiarism_ranges = []
            if question.question_type == QuestionType.long_answer and student_answer:
                plagiarism_ranges = self._extract_plagiarism_ranges_for_question(
                    student_answer.answer_text or "",
                    plagiarism_matches,
                    question_text_offsets.get(question.id)
                )
            
            question_data = self._build_question_review_data(
                question, 
                student_answer, 
                final_question_points,
                db,
                show_correct_answers,
                plagiarism_ranges
            )
            review_questions.append(question_data)
        
        return review_questions

    def _build_question_review_data(
            self,
            question: Question,
            student_answer: Answer | None,
            true_question_points: float,
            db: Session,
            show_correct_answers: bool = True,
            plagiarism_ranges: list = None
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
            return self._build_long_answer_data(base_data, student_answer, db, plagiarism_ranges or [])
            
        elif q_type == QuestionType.short_answer:
            return self._build_short_answer_data(base_data, question, student_answer, show_correct_answers)
            
        elif q_type == QuestionType.matching:
            return self._build_matching_data(base_data, question, student_answer, show_correct_answers)
            
        return base_data

    # --- Функції-конструктори для кожного типу питання ---

    @staticmethod
    def _build_single_choice_data(base_data, question, student_answer, show_correct_answers=True):
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

    @staticmethod
    def _build_multi_choice_data(base_data, question, student_answer, show_correct_answers=True):
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

    @staticmethod
    def _build_long_answer_data(base_data, student_answer, db: Session = None, plagiarism_ranges: list = None):
        # earned_points може бути встановлено вчителем вручну
        # Якщо earned_points встановлено в Answer, використовуємо його
        answer_id = str(student_answer.id) if student_answer else None
        # earned_points зберігається в масштабі final_points (масштабованих до 100 балів)
        earned_points = None
        # Перевіряємо, чи earned_points встановлено (включаючи 0)
        if student_answer and student_answer.earned_points is not None:
            # earned_points вже в правильному масштабі (final_points)
            # Важливо: 0 - це валідне значення, тому перевіряємо is not None, а не просто truthiness
            earned_points = float(student_answer.earned_points)
        
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
            is_flagged=is_flagged,
            plagiarism_ranges=plagiarism_ranges or []
        )
    
    @staticmethod
    def _extract_plagiarism_ranges_for_question(question_text: str, matches: list, question_offset: tuple = None) -> list:
        """
        Витягує ranges (start, end) сплагіачених частин тексту з matches для окремого питання.
        Перераховує ranges з об'єднаного тексту всіх питань на окреме питання.
        
        Args:
            question_text: Текст відповіді на окреме питання
            matches: Список matches з plagiarism_check.details
            question_offset: Tuple (start_offset, end_offset) позиції питання в об'єднаному тексті
        """
        if not matches or not question_text:
            return []
        
        import logging
        logger = logging.getLogger(__name__)
        
        all_ranges = ExamReviewService._extract_ranges_from_matches(matches)
        if not all_ranges:
            return []
        
        if question_offset is None:
            logger.warning("No question_offset provided, using ranges as-is (may be incorrect)")
            return ExamReviewService._filter_ranges_without_offset(all_ranges, question_text)
        
        question_ranges = ExamReviewService._map_ranges_with_offset(
            all_ranges, question_text, question_offset, logger
        )
        if not question_ranges:
            return []
        
        return ExamReviewService._merge_overlapping_ranges(question_ranges, question_text)
    
    @staticmethod
    def _extract_ranges_from_matches(matches: list) -> list:
        """Витягує всі ranges з matches."""
        all_ranges = []
        for match in matches:
            if "text_ranges" in match and match["text_ranges"]:
                all_ranges.extend(match["text_ranges"])
            elif "ranges" in match and match["ranges"]:
                all_ranges.extend(match["ranges"])
            elif "start" in match and "end" in match:
                all_ranges.append({"start": match["start"], "end": match["end"]})
        return all_ranges
    
    @staticmethod
    def _filter_ranges_without_offset(all_ranges: list, question_text: str) -> list:
        """Фільтрує ranges без offset, які потрапляють в межі тексту питання."""
        filtered_ranges = []
        for r in all_ranges:
            start = max(0, min(r.get("start", 0), len(question_text)))
            end = max(start, min(r.get("end", len(question_text)), len(question_text)))
            if start < end:
                filtered_ranges.append({"start": start, "end": end})
        return filtered_ranges
    
    @staticmethod
    def _map_ranges_with_offset(
        all_ranges: list, question_text: str, question_offset: tuple, logger
    ) -> list:
        """Перераховує ranges з об'єднаного тексту на окреме питання."""
        question_start, question_end = question_offset
        question_ranges = []
        
        for range_item in all_ranges:
            combined_start = range_item.get("start", 0)
            combined_end = range_item.get("end", 0)
            
            if combined_end <= question_start or combined_start >= question_end:
                continue
            
            question_range_start = max(0, combined_start - question_start)
            question_range_end = min(len(question_text), combined_end - question_start)
            
            if question_range_start < question_range_end:
                question_ranges.append({
                    "start": question_range_start,
                    "end": question_range_end
                })
        
        if not question_ranges:
            logger.debug(f"No ranges mapped to question text (offset: {question_offset})")
            return []
        
        question_ranges.sort(key=lambda r: r.get("start", 0))
        return question_ranges
    
    @staticmethod
    def _merge_overlapping_ranges(question_ranges: list, question_text: str) -> list:
        """Об'єднує перекриваючі ranges."""
        merged_ranges = []
        for range_item in question_ranges:
            start = max(0, min(range_item.get("start", 0), len(question_text)))
            end = max(start, min(range_item.get("end", len(question_text)), len(question_text)))
            
            if start >= end:
                continue
            
            if not merged_ranges:
                merged_ranges.append({"start": start, "end": end})
            else:
                last_range = merged_ranges[-1]
                if start <= last_range["end"]:
                    last_range["end"] = max(last_range["end"], end)
                else:
                    merged_ranges.append({"start": start, "end": end})
        
        return merged_ranges
    
    @staticmethod
    def _extract_plagiarism_ranges(text: str, matches: list) -> list:
        """
        Витягує ranges (start, end) сплагіачених частин тексту з matches.
        Очікує, що в matches є інформація про text_ranges або ranges.
        DEPRECATED: Використовуйте _extract_plagiarism_ranges_for_question для окремих питань.
        """
        if not matches or not text:
            return []
        
        import logging
        logger = logging.getLogger(__name__)
        
        ranges = ExamReviewService._extract_ranges_from_matches_with_logging(matches, logger)
        if not ranges:
            logger.debug(f"No ranges extracted from {len(matches)} matches")
            return []
        
        ranges.sort(key=lambda r: r.get("start", 0))
        merged_ranges = ExamReviewService._merge_overlapping_ranges(ranges, text)
        
        logger.debug(f"Extracted {len(merged_ranges)} merged ranges from {len(ranges)} original ranges")
        return merged_ranges
    
    @staticmethod
    def _extract_ranges_from_matches_with_logging(matches: list, logger) -> list:
        """Витягує ranges з matches з логуванням."""
        ranges = []
        for match in matches:
            if "text_ranges" in match and match["text_ranges"]:
                ranges.extend(match["text_ranges"])
                logger.debug(f"Found text_ranges in match: {match['text_ranges']}")
            elif "ranges" in match and match["ranges"]:
                ranges.extend(match["ranges"])
                logger.debug(f"Found ranges in match: {match['ranges']}")
            elif "start" in match and "end" in match:
                ranges.append({"start": match["start"], "end": match["end"]})
                logger.debug(f"Found start/end in match: {match['start']}-{match['end']}")
            else:
                logger.debug(f"No ranges found in match: {match.keys()}")
        return ranges
        
    @staticmethod
    def _build_short_answer_data(base_data, question, student_answer, show_correct_answers=True):
        # Отримуємо всі правильні відповіді
        correct_texts = [opt.text for opt in question.options if opt.is_correct]
        # Визначаємо, чи питання числове
        is_numeric = GradingService._is_numeric_question(correct_texts)
        # Нормалізуємо правильні відповіді
        correct_answers = {GradingService._normalize_short_answer(text, is_numeric) for text in correct_texts}
        
        student_ans_text = student_answer.answer_text if student_answer else ""
        # Нормалізуємо відповідь студента для перевірки
        normalized_student_answer = GradingService._normalize_short_answer(student_ans_text, is_numeric)
        earned_points = 0
        
        if normalized_student_answer in correct_answers:
            earned_points = base_data["points"]
        
        # Приховуємо правильну відповідь, якщо не дозволено показувати правильні відповіді
        # Беремо першу правильну відповідь у нормалізованому вигляді для відображення
        correct_answer_text = next(iter(correct_texts), None) if show_correct_answers else None
            
        return ShortAnswerQuestionReview(
            **base_data,
            student_answer_text=student_ans_text,
            correct_answer_text=correct_answer_text,
            earned_points=earned_points if show_correct_answers else None  # Приховуємо бали, якщо не показуємо правильні відповіді
        )
        
    @staticmethod
    def _build_matching_data(base_data, question, student_answer, show_correct_answers=True):
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
