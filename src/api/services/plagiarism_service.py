from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.repositories.plagiarism_repository import PlagiarismRepository
from src.models.attempts import Attempt, Answer, PlagiarismStatus
from src.models.exams import Question, QuestionType
from src.api.schemas.plagiarism import PlagiarismCheckSummary, PlagiarismComparisonResponse, PlagiarismReport, PlagiarismMatch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from src.models.paraphrase import ParaphraseModel
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class PlagiarismService:
    def __init__(
        self,
        repo: PlagiarismRepository,
        paraphrase_model: Optional[ParaphraseModel] = None,
    ) -> None:
        self.repo = repo
        self.paraphrase_model = paraphrase_model or ParaphraseModel()

    # ---------- ПУБЛІЧНИЙ ВХІДНИЙ МЕТОД ----------

    def check_attempt(self, db: Session, attempt: Attempt) -> PlagiarismReport:
        """
        Основний метод: запускається після submit спроби.
        Повертає PlagiarismReport і ПАРАЛЕЛЬНО зберігає результат в БД.
        Використовує обмеження часу для запобігання довгим операціям.
        """
        import time
        start_time = time.time()
        MAX_PROCESSING_TIME = 60  # Максимальний час обробки (секунди)
        
        try:
            # 1. Зібрати текст для цієї спроби (тільки long_answer)
            base_text = self._build_attempt_text(db, attempt.id)
            if not base_text.strip():
                # Немає long_answer — вважаємо 100% унікальність
                logger.info(f"Attempt {attempt.id} has no long_answer text, skipping plagiarism check")
                check = self.repo.create_or_update(
                    db,
                    attempt_id=attempt.id,
                    uniqueness_percent=100.0,
                    max_similarity=0.0,
                    status=PlagiarismStatus.ok,
                    details={"matches": []},
                )
                return self._to_report(check)

            # 2. Знайти кандидатів серед інших спроб цього ж іспиту
            candidate_attempt_ids, candidate_texts = self._get_candidate_attempt_texts(
                db, exam_id=attempt.exam_id, exclude_attempt_id=attempt.id
            )

            if not candidate_attempt_ids:
                # Нема з чим порівнювати — унікальність 100%
                logger.info(f"No candidate attempts found for attempt {attempt.id}")
                check = self.repo.create_or_update(
                    db,
                    attempt_id=attempt.id,
                    uniqueness_percent=100.0,
                    max_similarity=0.0,
                    status=PlagiarismStatus.ok,
                    details={"matches": []},
                )
                return self._to_report(check)

            # Перевірка часу виконання
            elapsed = time.time() - start_time
            if elapsed > MAX_PROCESSING_TIME:
                logger.warning(f"Plagiarism check for attempt {attempt.id} exceeded time limit, using fast check only")
                # Повертаємо результат на основі швидкої перевірки
                fast_matches = self._run_fast_tfidf_filter(
                    base_text, candidate_texts, candidate_attempt_ids, db
                )
                max_similarity = max([m["similarity_score"] for m in fast_matches], default=0.0)
                uniqueness = max(0.0, 100.0 - max_similarity * 100.0)
                status = self._status_from_similarity(max_similarity)
                check = self.repo.create_or_update(
                    db,
                    attempt_id=attempt.id,
                    uniqueness_percent=uniqueness,
                    max_similarity=max_similarity,
                    status=status,
                    details={"matches": fast_matches, "level": "fast", "timeout": True},
                )
                return self._to_report(check)

            # 3. Рівень 1: TF-IDF + cosine
            fast_matches = self._run_fast_tfidf_filter(
                base_text, candidate_texts, candidate_attempt_ids, db
            )

            # Якщо є явний копіпаст (>0.98) — глибокий аналіз необов'язковий
            exact_match = next(
                (m for m in fast_matches if m["similarity_score"] >= 0.98), None
            )
            if exact_match:
                max_sim = exact_match["similarity_score"]
                uniqueness = max(0.0, 100.0 - max_sim * 100.0)
                status = self._status_from_similarity(max_sim)

                check = self.repo.create_or_update(
                    db,
                    attempt_id=attempt.id,
                    uniqueness_percent=uniqueness,
                    max_similarity=max_sim,
                    status=status,
                    details={"matches": fast_matches, "level": "fast"},
                )
                return self._to_report(check)

            # Перевірка часу перед глибоким аналізом
            elapsed = time.time() - start_time
            if elapsed > MAX_PROCESSING_TIME * 0.7:  # Якщо вже витрачено 70% часу, пропускаємо глибокий аналіз
                logger.info(f"Skipping deep analysis for attempt {attempt.id} due to time constraints")
                final_matches = fast_matches
            else:
                # 4. Рівень 2: глибокий семантичний аналіз (парафрази)
                deep_matches, _ = self._run_deep_semantic_analysis(
                    db, base_text, fast_matches
                )
                # Якщо глибокий аналіз нічого не додав — використовуємо fast рівень
                final_matches = deep_matches or fast_matches

            max_similarity = max(
                [m["similarity_score"] for m in final_matches], default=0.0
            )
            uniqueness = max(0.0, 100.0 - max_similarity * 100.0)
            status = self._status_from_similarity(max_similarity)

            check = self.repo.create_or_update(
                db,
                attempt_id=attempt.id,
                uniqueness_percent=uniqueness,
                max_similarity=max_similarity,
                status=status,
                details={"matches": final_matches, "level": "deep" if final_matches != fast_matches else "fast"},
            )

            elapsed_total = time.time() - start_time
            logger.info(f"Plagiarism check completed for attempt {attempt.id} in {elapsed_total:.2f}s")
            return self._to_report(check)
        except Exception as e:
            logger.error(f"Error during plagiarism check for attempt {attempt.id}: {str(e)}", exc_info=True)
            # Повертаємо безпечний результат у разі помилки
            check = self.repo.create_or_update(
                db,
                attempt_id=attempt.id,
                uniqueness_percent=100.0,
                max_similarity=0.0,
                status=PlagiarismStatus.ok,
                details={"matches": [], "error": str(e)},
            )
            return self._to_report(check)

    # ---------- ДОПОМІЖНІ МЕТОДИ ДЛЯ TEКСТУ ----------

    @staticmethod
    def _build_attempt_text(db: Session, attempt_id: UUID) -> str:
        """
        Формує "текст роботи" зі всіх відповідей типу long_answer цієї спроби.
        """
        rows: List[Tuple[str]] = (
            db.query(Answer.answer_text)
            .join(Question, Question.id == Answer.question_id)
            .filter(
                Answer.attempt_id == attempt_id,
                Question.question_type == QuestionType.long_answer,
                Answer.answer_text.isnot(None),
            )
            .all()
        )
        texts = [t[0] for t in rows if t[0]]
        return "\n\n".join(texts)

    def _get_candidate_attempt_texts(
        self, db: Session, *, exam_id: UUID, exclude_attempt_id: UUID
    ) -> Tuple[List[UUID], List[str]]:
        """
        Знаходимо всі інші спроби цього іспиту, у яких є long_answer-відповіді.
        Повертаємо списки attempt_ids і відповідних текстів.
        """
        # Знаходимо всі спроби цього екзамену, крім поточної
        attempts_with_long = (
            db.query(Attempt.id)
            .join(Answer, Answer.attempt_id == Attempt.id)
            .join(Question, Question.id == Answer.question_id)
            .filter(
                Attempt.exam_id == exam_id,
                Attempt.id != exclude_attempt_id,
                Question.question_type == QuestionType.long_answer,
                Answer.answer_text.isnot(None),
            )
            .distinct()
            .all()
        )
        attempt_ids = [row[0] for row in attempts_with_long]

        texts: List[str] = []
        for aid in attempt_ids:
            texts.append(self._build_attempt_text(db, aid))

        return attempt_ids, texts

    # ---------- РІВЕНЬ 1: TF-IDF + COSINE ----------

    def _run_fast_tfidf_filter(
        self,
        base_text: str,
        candidate_texts: List[str],
        candidate_ids: List[UUID],
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Будує TF-IDF матрицю і повертає список матчів за косинусною подібністю.
        """
        if not base_text or not base_text.strip():
            logger.warning("_run_fast_tfidf_filter called with empty base_text")
            return []
        if not candidate_texts:
            logger.debug("_run_fast_tfidf_filter called with empty candidate_texts")
            return []
        
        corpus = [base_text] + candidate_texts
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError as e:
            # Наприклад, якщо всі тексти порожні або надто короткі
            logger.warning(f"TF-IDF vectorization failed: {str(e)}")
            return []

        base_vec = tfidf_matrix[0:1]
        other_vecs = tfidf_matrix[1:]

        similarities = cosine_similarity(base_vec, other_vecs)[0]  # shape: (n_candidates,)

        matches: List[Dict[str, Any]] = []
        for idx, sim in enumerate(similarities):
            match_data = {
                "other_attempt_id": str(candidate_ids[idx]),
                "similarity_score": float(sim),
                "match_type": "exact" if sim >= 0.98 else "candidate",
            }
            
            # Для високої схожості генеруємо ranges для виділення
            if sim >= 0.5 and db:  # Тільки для значущої схожості та якщо є доступ до db
                try:
                    other_text = candidate_texts[idx] if idx < len(candidate_texts) else None
                    if other_text and other_text.strip():
                        base_spans, _ = self._compute_highlight_spans(base_text, other_text, min_match_len=10)
                        # Конвертуємо spans (tuple) в ranges (dict)
                        if base_spans:
                            match_data["ranges"] = [{"start": span[0], "end": span[1]} for span in base_spans]
                except Exception as e:
                    logger.warning(f"Failed to compute highlight spans for match {candidate_ids[idx]}: {e}")
            
            matches.append(match_data)

        # Сортуємо за спаданням схожості
        matches.sort(key=lambda m: m["similarity_score"], reverse=True)
        return matches

    # ---------- РІВЕНЬ 2: ГЛИБОКИЙ АНАЛІЗ (ЗАГЛУШКА) ----------

    def _run_deep_semantic_analysis(
        self,
        db: Session,
        base_text: str,
        fast_matches: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Рівень 2: справжній семантичний аналіз через ParaphraseModel.
        Для кожного кандидата з fast-матчів будуємо текст іншої спроби
        і рахуємо семантичну схожість.
        """

        if not fast_matches:
            return [], 0.0

        # Беремо тільки топ-кандидатів, щоб не вантажити модель на сотні текстів
        top_candidates = [m for m in fast_matches if m["similarity_score"] >= 0.2][:5]

        deep_results: List[Dict[str, Any]] = []
        max_sim = 0.0

        for m in top_candidates:
            other_attempt_id = UUID(m["other_attempt_id"])
            other_text = self._build_attempt_text(db, other_attempt_id)

            if not other_text.strip():
                continue

            # Семантична схожість з нейромережею
            semantic_sim = self.paraphrase_model.similarity(base_text, other_text)

            deep_match = {
                "other_attempt_id": m["other_attempt_id"],
                "similarity_score": float(semantic_sim),
                "match_type": "paraphrase" if semantic_sim >= 0.7 else "candidate",
            }
            
            # Генеруємо ranges для виділення сплагіачених частин
            if semantic_sim >= 0.5:  # Тільки для значущої схожості
                try:
                    base_spans, _ = self._compute_highlight_spans(base_text, other_text, min_match_len=10)
                    # Конвертуємо spans (tuple) в ranges (dict)
                    deep_match["ranges"] = [{"start": span[0], "end": span[1]} for span in base_spans]
                except Exception as e:
                    logger.warning(f"Failed to compute highlight spans for deep match {other_attempt_id}: {e}")
            
            deep_results.append(deep_match)
            max_sim = max(max_sim, semantic_sim)

        deep_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return deep_results, max_sim


    # ---------- ДОПОМІЖНЕ: статус + конвертація в Pydantic ----------

    @staticmethod
    def _status_from_similarity(similarity: float) -> PlagiarismStatus:
        """
        Можеш підкрутити пороги як хочеш.
        """
        if similarity >= 0.9:
            return PlagiarismStatus.high_risk
        if similarity >= 0.7:
            return PlagiarismStatus.suspicious
        return PlagiarismStatus.ok

    @staticmethod
    def _to_report(check) -> PlagiarismReport:
        matches_raw = (check.details or {}).get("matches", [])
        matches: List[PlagiarismMatch] = [
            PlagiarismMatch(
                other_attempt_id=UUID(m["other_attempt_id"]),
                similarity_score=m["similarity_score"],
                match_type=m["match_type"],
            )
            for m in matches_raw
        ]
        return PlagiarismReport(
            uniqueness_percent=check.uniqueness_percent,
            status=check.status.value if hasattr(check.status, "value") else str(check.status),
            matches=matches,
        )
    
        # ---------- ПУБЛІЧНІ ЗАПИТИ ДЛЯ ВИКЛАДАЧА ----------

    def list_exam_checks(
        self,
        db: Session,
        exam_id: UUID,
        max_uniqueness: Optional[float] = None,
    ) -> List[PlagiarismCheckSummary]:
        """
        Повертає список результатів перевірки на плагіат по іспиту,
        з можливим фільтром max_uniqueness (наприклад, <= 70).
        """
        checks = self.repo.list_by_exam_with_filter(
            db,
            exam_id=exam_id,
            max_uniqueness=max_uniqueness,
        )

        results: List[PlagiarismCheckSummary] = []
        for ch in checks:
            # ch.attempt має бути доступний через relationship
            attempt: Attempt = ch.attempt
            results.append(
                PlagiarismCheckSummary(
                    attempt_id=attempt.id,
                    student_id=attempt.user_id,
                    uniqueness_percent=ch.uniqueness_percent,
                    max_similarity=ch.max_similarity,
                    status=ch.status.value if hasattr(ch.status, "value") else str(ch.status),
                )
            )
        return results

    def compare_attempts_texts(
        self,
        db: Session,
        base_attempt_id: UUID,
        other_attempt_id: UUID,
    ) -> PlagiarismComparisonResponse:
        """
        Повертає тексти long_answer для двох спроб та їх семантичну схожість
        (через ParaphraseModel).
        """
        base_text = self._build_attempt_text(db, base_attempt_id)
        other_text = self._build_attempt_text(db, other_attempt_id)

        similarity_score = self.paraphrase_model.similarity(base_text, other_text)

        return PlagiarismComparisonResponse(
            base_attempt_id=base_attempt_id,
            other_attempt_id=other_attempt_id,
            base_text=base_text,
            other_text=other_text,
            similarity_score=similarity_score,
        )
    
    def get_comparison(
        self,
        db: Session,
        *,
        base_attempt_id: UUID,
        other_attempt_id: UUID,
    ) -> PlagiarismComparisonResponse:
        """
        Повертає тексти двох спроб (long_answer-відповіді) + оцінку схожості
        та діапазони збігів для підсвітки.
        """
        base_text = self._build_attempt_text(db, base_attempt_id)
        other_text = self._build_attempt_text(db, other_attempt_id)

        if not base_text.strip() or not other_text.strip():
            similarity_score = 0.0
            base_spans: List[Tuple[int, int]] = []
            other_spans: List[Tuple[int, int]] = []
        else:
            # Використовуємо нейромережу для оцінки загальної схожості
            similarity_score = self.paraphrase_model.similarity(base_text, other_text)
            # А для підсвітки — SequenceMatcher
            base_spans, other_spans = self._compute_highlight_spans(base_text, other_text)

        return PlagiarismComparisonResponse(
            base_attempt_id=base_attempt_id,
            other_attempt_id=other_attempt_id,
            base_text=base_text,
            other_text=other_text,
            similarity_score=similarity_score,
            base_highlight_spans=base_spans,
            other_highlight_spans=other_spans,
        )
    
    @staticmethod
    def _compute_highlight_spans(
        base_text: str,
        other_text: str,
        min_match_len: int = 20,
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Шукає однакові фрагменти між base_text та other_text
        і повертає списки span'ів для підсвітки.
        min_match_len — мінімальна довжина фрагмента, щоб його підсвічувати.
        """
        matcher = SequenceMatcher(None, base_text, other_text)
        base_spans: List[Tuple[int, int]] = []
        other_spans: List[Tuple[int, int]] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            # Нас цікавлять тільки однакові фрагменти достатньої довжини
            if tag == "equal" and (i2 - i1) >= min_match_len:
                base_spans.append((i1, i2))
                other_spans.append((j1, j2))

        return base_spans, other_spans

