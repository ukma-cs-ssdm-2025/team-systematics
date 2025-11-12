from sqlalchemy.orm import Session, joinedload, selectinload, load_only
from typing import Optional, List
from sqlalchemy import func
from uuid import UUID

from src.api.repositories.attempts_repository import AttemptsRepository
from src.api.services.grading_service import GradingService
from src.api.repositories.weights_repository import WeightsRepository
from src.api.schemas.attempts import (
    AnswerUpsert,
    Answer as AnswerSchema,
    Attempt as AttemptSchema,
    AttemptResultResponse,
    AnswerScoreUpdate,
    AddTimeRequest,
    ActiveAttemptInfo
)

from src.api.schemas.plagiarism import (
    PlagiarismReport,
    PlagiarismCheckSummary,
    PlagiarismComparisonResponse,
)

from src.models.attempts import Attempt, AttemptStatus, Answer
from src.models.exams import Exam, Question, QuestionType
from src.api.errors.app_errors import NotFoundError, ConflictError, ForbiddenError
from src.utils.largest_remainder import distribute_largest_remainder

from src.api.services.plagiarism_service import PlagiarismService
from src.api.repositories.plagiarism_repository import PlagiarismRepository
from src.api.repositories.flagged_answers_repository import FlaggedAnswersRepository
from src.api.schemas.plagiarism import FlaggedAnswerResponse, AnswerComparisonResponse
from src.models.users import User
from src.models.user_roles import UserRole
from src.models.paraphrase import ParaphraseModel

# Introduce Constant / Replace Magic Literal
ATTEMPT_NOT_FOUND_MSG = "Attempt not found"
TEACHER_ROLE_ID = 2

class AttemptsService:
    def __init__(self, plagiarism_service: Optional[PlagiarismService] = None) -> None:
        if plagiarism_service:
            self.plagiarism_service = plagiarism_service
        else:
            self.plagiarism_service = PlagiarismService(
                repo=PlagiarismRepository(),
                paraphrase_model=ParaphraseModel(),
            )

    def add_answer(
        self, db: Session, attempt_id: UUID, payload: AnswerUpsert
    ) -> AnswerSchema:
        repo = AttemptsRepository(db)
        att = repo.get_attempt(attempt_id)
        if not att:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        if att.status != "in_progress":
            raise ConflictError("Attempt is locked or submitted")
        
        answer = repo.upsert_answer(attempt_id, payload)
        
        # Конвертуємо SQLAlchemy модель у Pydantic схему
        # Отримуємо selected_option_ids для MCQ питань
        selected_option_ids = None
        if answer.selected_options:
            selected_option_ids = [opt.selected_option_id for opt in answer.selected_options]
        
        return AnswerSchema(
            id=answer.id,
            attempt_id=answer.attempt_id,
            question_id=answer.question_id,
            text=answer.answer_text,
            selected_option_ids=selected_option_ids,
            saved_at=answer.saved_at
        )

    def submit(self, db: Session, attempt_id: UUID) -> AttemptSchema:
        """
        Завершує спробу, запускає повний процес оцінювання та зберігає результати.
        """
        repo = AttemptsRepository(db)
        grading_service = GradingService()

        attempt = db.query(Attempt).filter(Attempt.id == attempt_id).options(
            joinedload(Attempt.exam).selectinload(Exam.questions).selectinload(Question.options),
            joinedload(Attempt.exam).selectinload(Exam.questions).selectinload(Question.matching_options),
            selectinload(Attempt.answers).joinedload(Answer.question),
            selectinload(Attempt.answers).selectinload(Answer.selected_options)
        ).one_or_none()

        if not attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        if attempt.status != AttemptStatus.in_progress:
            raise ConflictError("Attempt is already submitted")

        repo.submit_attempt(attempt.id)

        # Викликаємо сервіс оцінювання, який поверне нам статистику
        grading_result = grading_service.calculate_score(db, attempt)
        
        # Обчислюємо загальну вагу іспиту для розрахунку фінальної оцінки
        total_exam_weight = db.query(func.sum(Question.points)).filter(
            Question.exam_id == attempt.exam_id
        ).scalar() or 0.0

        final_score = 0.0
        if total_exam_weight > 0:
            final_score = (grading_result.earned_weight / total_exam_weight) * 100

        final_score = min(100.0, final_score)

        attempt.correct_answers = grading_result.correct_count
        attempt.incorrect_answers = grading_result.incorrect_count
        attempt.pending_count = grading_result.pending_count
        attempt.earned_points = final_score

        if grading_result.pending_count > 0:
            attempt.status = AttemptStatus.submitted
        else:
            attempt.status = AttemptStatus.completed

        # Автоматична перевірка на плагіат (тільки long_answer всередині сервісу)
        self.plagiarism_service.check_attempt(db, attempt)

        db.commit()
        db.refresh(attempt)

        return attempt    

    def get_attempt_details(self, db: Session, attempt_id: UUID):
        repo = AttemptsRepository(db)
        att = repo.get_attempt_with_details(attempt_id)
        if not att:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        return att

    def get_attempt_result(
        self,
        db: Session,
        attempt_id: UUID,
    ) -> AttemptResultResponse:
        """
        Отримує вже обчислені результати спроби та форматує їх для відповіді API.
        """
        repo = AttemptsRepository(db)
        data = repo.get_attempt_result_raw(attempt_id)
        if not data:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)

        status = data["attempt_status"]
        if data["pending_count"] == 0 and status == "submitted":
            status = "completed"

        return AttemptResultResponse(
            exam_title=data["exam_title"],
            status=status,
            score=float(data["score"]),
            time_spent_seconds=data["time_spent_seconds"],
            total_questions=data["total_questions"],
            answers_given=data["answers_given"],
            correct_answers=data["correct_answers"],
            incorrect_answers=data["incorrect_answers"],
            pending_count=data["pending_count"]
        )

    def update_answer_score(
        self, 
        db: Session, 
        attempt_id: UUID, 
        answer_id: UUID, 
        payload: AnswerScoreUpdate,
        max_points: float
    ) -> AnswerSchema:
        """
        Оновлює оцінку для відповіді на long_answer питання.
        Валідує, що оцінка не перевищує максимальну та не від'ємна.
        earned_points зберігається в масштабі final_points (масштабованих до 100 балів системи).
        Перераховує загальну оцінку та перевіряє, чи всі long_answer оцінені.
        """
        # Валідація оцінки
        if payload.earned_points < 0:
            raise ValueError("Оцінка не може бути від'ємною")
        if payload.earned_points > max_points:
            raise ValueError(f"Оцінка не може перевищувати максимальну ({max_points})")
        
        # Завантажуємо attempt з усіма даними для розрахунку масштабу
        attempt = db.query(Attempt).options(
            joinedload(Attempt.exam).selectinload(Exam.questions),
            selectinload(Attempt.answers).joinedload(Answer.question)
        ).filter(Attempt.id == attempt_id).first()
        
        if not attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        
        # Знаходимо відповідь та питання
        answer = None
        question = None
        for ans in attempt.answers:
            if ans.id == answer_id:
                answer = ans
                question = ans.question
                break
        
        if not answer or not question:
            raise NotFoundError("Answer or question not found")
        
        if question.question_type != QuestionType.long_answer:
            raise ValueError("Цей endpoint призначений тільки для long_answer питань")
        
        # Розраховуємо final_points для цього питання (масштабовані до 100 балів)
        weights_repo = WeightsRepository(db)
        weights_map = weights_repo.get_all_weights()
        
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
        
        final_points_map = distribute_largest_remainder(true_points_map, target_total=100)
        question_final_points = final_points_map.get(question.id, 0)
        
        # Зберігаємо earned_points в БД для long_answer питань
        # Оскільки це ручна оцінка вчителя, вона має зберігатися
        earned_points_to_save = min(payload.earned_points, question_final_points)
        earned_points_to_save = max(0.0, earned_points_to_save)  # Не може бути від'ємним
        
        # Оновлюємо оцінку (в масштабі final_points)
        answer.earned_points = earned_points_to_save
        db.commit()
        
        # Перераховуємо загальну оцінку
        self._recalculate_attempt_score(db, attempt)
        
        # Перевіряємо, чи всі long_answer питання оцінені
        self._check_and_update_attempt_status(db, attempt)
        
        db.refresh(answer)
        return AnswerSchema(
            id=answer.id,
            attempt_id=answer.attempt_id,
            question_id=answer.question_id,
            text=answer.answer_text,
            selected_option_ids=None,  # Не використовується для long_answer
            saved_at=answer.saved_at
        )
    
    def _calculate_final_points_map(self, db: Session, attempt: Attempt) -> dict:
        """Розраховує фінальну мапу балів для питань (масштабовані до 100 балів)."""
        weights_repo = WeightsRepository(db)
        weights_map = weights_repo.get_all_weights()
        
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
    
    def _calculate_long_answer_score(self, answer: Answer) -> float:
        """Розраховує бали для long_answer питання."""
        if answer and answer.earned_points is not None:
            return answer.earned_points
        return 0.0
    
    def _calculate_auto_graded_score(
        self, 
        question: Question, 
        answer: Answer, 
        question_points: float,
        grading_service: GradingService,
        correct_data: dict
    ) -> float:
        """Розраховує бали для автоматично оцінюваних питань."""
        if not answer:
            return 0.0
        
        base_question_points = float(question.points or 0.0)
        if base_question_points == 0:
            return 0.0
        
        # Визначаємо метод оцінювання залежно від типу питання
        grading_methods = {
            QuestionType.single_choice: grading_service._grade_single_choice,
            QuestionType.multi_choice: grading_service._grade_multi_choice,
            QuestionType.short_answer: grading_service._grade_short_answer,
            QuestionType.matching: grading_service._grade_matching,
        }
        
        grade_method = grading_methods.get(question.question_type)
        if not grade_method:
            return 0.0
        
        earned_base, _ = grade_method(question, answer, correct_data.get(question.id, {}))
        earned_scaled = (earned_base / base_question_points) * question_points
        return earned_scaled
    
    def _recalculate_attempt_score(self, db: Session, attempt: Attempt) -> None:
        """
        Перераховує загальну оцінку для спроби на основі всіх оцінок за питання.
        Використовує ту саму логіку, що й exam_review_service для консистентності.
        earned_points зберігається в масштабі points питання (які вже масштабовані до 100 балів).
        """
        final_points_map = self._calculate_final_points_map(db, attempt)
        answers_map = {ans.question_id: ans for ans in attempt.answers}
        
        grading_service = GradingService()
        correct_data = grading_service._build_correct_data(attempt.exam)
        
        total_earned = 0.0
        for question in attempt.exam.questions:
            answer = answers_map.get(question.id)
            question_points = final_points_map.get(question.id, 0)
            
            if question.question_type == QuestionType.long_answer:
                total_earned += self._calculate_long_answer_score(answer)
            else:
                total_earned += self._calculate_auto_graded_score(
                    question, answer, question_points, grading_service, correct_data
                )
        
        attempt.earned_points = min(100.0, max(0.0, total_earned))
        db.commit()
    
    def _check_and_update_attempt_status(self, db: Session, attempt: Attempt) -> None:
        """
        Перевіряє, чи всі long_answer питання оцінені.
        Якщо так, і статус submitted, змінює статус на completed.
        """
        # Знаходимо всі long_answer питання
        long_answer_questions = [q for q in attempt.exam.questions if q.question_type == QuestionType.long_answer]
        
        if not long_answer_questions:
            return
        
        # Перевіряємо, чи всі long_answer питання мають відповіді з оцінками
        answers_map = {ans.question_id: ans for ans in attempt.answers}
        all_graded = True
        
        for question in long_answer_questions:
            answer = answers_map.get(question.id)
            if not answer or answer.earned_points is None:
                all_graded = False
                break
        
        # Якщо всі long_answer оцінені і статус submitted, змінюємо на completed
        if all_graded and attempt.status == AttemptStatus.submitted:
            attempt.status = AttemptStatus.completed
            attempt.pending_count = 0
            db.commit()

    def _is_teacher(self, db: Session, user: User) -> bool:
        """
        Перевіряємо, чи має користувач роль викладача через таблицю user_roles.
        TEACHER_ROLE_ID = 2.
        """
        return (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user.id,
                UserRole.role_id == TEACHER_ROLE_ID,
            )
            .first()
            is not None
        )
    
    def get_exam_plagiarism_checks(
        self,
        db: Session,
        exam_id: UUID,
        current_user: User,
        max_uniqueness: Optional[float] = None,
    ) -> List[PlagiarismCheckSummary]:
        """
        Список результатів перевірки на плагіат по іспиту (лише викладач).
        """
        if not self._is_teacher(db, current_user):
            # Якщо нема окремої ForbiddenError – використовуємо ConflictError
            raise ConflictError("Only teacher can view plagiarism checks")

        return self.plagiarism_service.list_exam_checks(
            db=db,
            exam_id=exam_id,
            max_uniqueness=max_uniqueness,
        )

    def get_attempts_comparison(
        self,
        db: Session,
        base_attempt_id: UUID,
        other_attempt_id: UUID,
        current_user: User,
    ) -> PlagiarismComparisonResponse:
        """
        Порівняння текстів двох спроб (лише викладач).
        """
        if not self._is_teacher(db, current_user):
            raise ConflictError("Only teacher can compare attempts for plagiarism")

        # Можна додатково перевірити, що обидві спроби існують:
        base = db.query(Attempt).filter(Attempt.id == base_attempt_id).one_or_none()
        other = db.query(Attempt).filter(Attempt.id == other_attempt_id).one_or_none()
        if not base or not other:
            raise NotFoundError("One or both attempts not found")

        return self.plagiarism_service.compare_attempts_texts(
            db=db,
            base_attempt_id=base_attempt_id,
            other_attempt_id=other_attempt_id,
        )
    
    def flag_answer_for_plagiarism_check(
        self,
        db: Session,
        answer_id: UUID,
        current_user: User,
    ) -> FlaggedAnswerResponse:
        """Позначити відповідь для перевірки на плагіат (тільки для вчителя)"""
        if not self._is_teacher(db, current_user):
            raise ForbiddenError("Only teachers can flag answers for plagiarism check")
        
        # Перевіряємо, чи існує відповідь та чи це long_answer
        answer = (
            db.query(Answer)
            .options(joinedload(Answer.question), joinedload(Answer.attempt))
            .filter(Answer.id == answer_id)
            .one_or_none()
        )
        
        if not answer:
            raise NotFoundError("Answer not found")
        
        if answer.question.question_type != QuestionType.long_answer:
            raise ValueError("Можна позначити тільки відповіді типу long_answer")
        
        repo = FlaggedAnswersRepository()
        
        # Перевіряємо, чи вже позначена
        if repo.is_flagged(db, answer_id):
            raise ConflictError("Answer is already flagged")
        
        # Створюємо позначення
        flagged = repo.create(db, answer_id)
        db.commit()
        
        # Отримуємо повну інформацію
        attempt = answer.attempt
        exam = attempt.exam
        student = attempt.user
        
        return FlaggedAnswerResponse(
            answer_id=answer.id,
            attempt_id=attempt.id,
            question_id=answer.question_id,
            student_name=f"{student.first_name} {student.last_name}".strip(),
            exam_title=exam.title,
            exam_id=exam.id,
            answer_text=answer.answer_text or "",
            flagged_at=flagged.flagged_at.isoformat(),
        )
    
    def unflag_answer(
        self,
        db: Session,
        answer_id: UUID,
        current_user: User,
    ) -> None:
        """Зняти позначення з відповіді (тільки для вчителя)"""
        if not self._is_teacher(db, current_user):
            raise ForbiddenError("Only teachers can unflag answers")
        
        repo = FlaggedAnswersRepository()
        if not repo.delete(db, answer_id):
            raise NotFoundError("Flagged answer not found")
        db.commit()
    
    def list_flagged_answers(
        self,
        db: Session,
        current_user: User,
    ) -> List[FlaggedAnswerResponse]:
        """Отримати список всіх позначених відповідей (тільки для вчителя)"""
        if not self._is_teacher(db, current_user):
            raise ForbiddenError("Only teachers can view flagged answers")
        
        repo = FlaggedAnswersRepository()
        flagged_list = repo.list_all(db)
        
        results = []
        for flagged in flagged_list:
            answer = flagged.answer
            attempt = answer.attempt
            exam = attempt.exam
            student = attempt.user
            
            results.append(FlaggedAnswerResponse(
                answer_id=answer.id,
                attempt_id=attempt.id,
                question_id=answer.question_id,
                student_name=f"{student.first_name} {student.last_name}".strip(),
                exam_title=exam.title,
                exam_id=exam.id,
                answer_text=answer.answer_text or "",
                flagged_at=flagged.flagged_at.isoformat(),
            ))
        
        return results
    
    def compare_two_answers(
        self,
        db: Session,
        answer1_id: UUID,
        answer2_id: UUID,
        current_user: User,
    ) -> AnswerComparisonResponse:
        """Порівняти дві конкретні відповіді на плагіат (тільки для вчителя)"""
        if not self._is_teacher(db, current_user):
            raise ForbiddenError("Only teachers can compare answers")
        
        # Отримуємо відповіді з повною інформацією
        answer1 = (
            db.query(Answer)
            .options(
                joinedload(Answer.question),
                joinedload(Answer.attempt).joinedload(Attempt.user), 
                joinedload(Answer.attempt).joinedload(Attempt.exam)
            )
            .filter(Answer.id == answer1_id)
            .one_or_none()
        )
        
        answer2 = (
            db.query(Answer)
            .options(
                joinedload(Answer.question),
                joinedload(Answer.attempt).joinedload(Attempt.user), 
                joinedload(Answer.attempt).joinedload(Attempt.exam)
            )
            .filter(Answer.id == answer2_id)
            .one_or_none()
        )
        
        if not answer1 or not answer2:
            raise NotFoundError("One or both answers not found")
        
        # Перевіряємо, що обидві відповіді long_answer
        if answer1.question.question_type != QuestionType.long_answer or \
           answer2.question.question_type != QuestionType.long_answer:
            raise ValueError("Можна порівнювати тільки відповіді типу long_answer")
        
        # Отримуємо тексти відповідей
        text1 = answer1.answer_text or ""
        text2 = answer2.answer_text or ""
        
        # Використовуємо ParaphraseModel для порівняння
        paraphrase_model = ParaphraseModel()
        similarity_score = paraphrase_model.similarity(text1, text2)
        
        student1 = answer1.attempt.user
        student2 = answer2.attempt.user
        exam = answer1.attempt.exam  # Припускаємо, що обидві відповіді з одного іспиту
        
        return AnswerComparisonResponse(
            answer1_id=answer1.id,
            answer2_id=answer2.id,
            answer1_text=text1,
            answer2_text=text2,
            similarity_score=similarity_score,
            student1_name=f"{student1.first_name} {student1.last_name}".strip(),
            student2_name=f"{student2.first_name} {student2.last_name}".strip(),
            exam_title=exam.title,
        )

    def add_time_to_attempt(
        self,
        db: Session,
        attempt_id: UUID,
        payload: AddTimeRequest,
    ) -> AttemptSchema:
        """
        Додає додатковий час до спроби студента (тільки для наглядача).
        Перевірка ролі виконується в контролері через require_role('supervisor').
        """
        repo = AttemptsRepository(db)
        attempt = repo.add_time_to_attempt(attempt_id, payload.additional_minutes)
        
        if not attempt:
            raise NotFoundError(ATTEMPT_NOT_FOUND_MSG)
        
        return AttemptSchema(
            id=attempt.id,
            exam_id=attempt.exam_id,
            user_id=attempt.user_id,
            status=attempt.status.value,
            started_at=attempt.started_at,
            due_at=attempt.due_at,
            submitted_at=attempt.submitted_at,
            score_percent=attempt.earned_points,
            time_spent_seconds=attempt.time_spent_seconds,
        )

    def get_active_attempts_for_exam(
        self,
        db: Session,
        exam_id: UUID,
    ) -> List[ActiveAttemptInfo]:
        """
        Отримує список активних спроб для іспиту (тільки для наглядача).
        Перевірка ролі виконується в контролері через require_role('supervisor').
        """
        repo = AttemptsRepository(db)
        attempts = repo.get_active_attempts_for_exam(exam_id)
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        result = []
        for attempt in attempts:
            remaining_seconds = max(0, int((attempt.due_at - now).total_seconds()))
            remaining_minutes = remaining_seconds // 60
            
            user_full_name = f"{attempt.user.first_name} {attempt.user.last_name} {attempt.user.patronymic or ''}".strip()
            
            result.append(ActiveAttemptInfo(
                attempt_id=attempt.id,
                user_id=attempt.user_id,
                user_full_name=user_full_name,
                started_at=attempt.started_at,
                due_at=attempt.due_at,
                remaining_minutes=remaining_minutes,
                status=attempt.status.value,
            ))
        
        return result
    
