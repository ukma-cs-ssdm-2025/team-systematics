from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.repositories.plagiarism_repository import PlagiarismRepository
from src.models.attempts import Attempt, Answer, PlagiarismStatus
from src.models.exams import Question, QuestionType
from src.api.schemas.plagiarism import PlagiarismReport, PlagiarismMatch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from src.models.paraphrase import ParaphraseModel


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
        """

        # 1. Зібрати текст для цієї спроби (тільки long_answer)
        base_text = self._build_attempt_text(db, attempt.id)
        if not base_text.strip():
            # Немає long_answer — вважаємо 100% унікальність
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
            check = self.repo.create_or_update(
                db,
                attempt_id=attempt.id,
                uniqueness_percent=100.0,
                max_similarity=0.0,
                status=PlagiarismStatus.ok,
                details={"matches": []},
            )
            return self._to_report(check)

        # 3. Рівень 1: TF-IDF + cosine
        fast_matches = self._run_fast_tfidf_filter(
            base_text, candidate_texts, candidate_attempt_ids
        )

        # Якщо є явний копіпаст (>0.98) — глибокий аналіз необов’язковий
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

        # 4. Рівень 2: глибокий семантичний аналіз (парафрази)
        deep_matches, max_semantic_sim = self._run_deep_semantic_analysis(
            base_text, fast_matches
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
            details={"matches": final_matches, "level": "deep"},
        )

        return self._to_report(check)

    # ---------- ДОПОМІЖНІ МЕТОДИ ДЛЯ TEКСТУ ----------

    def _build_attempt_text(self, db: Session, attempt_id: UUID) -> str:
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
    ) -> List[Dict[str, Any]]:
        """
        Будує TF-IDF матрицю і повертає список матчів за косинусною подібністю.
        """
        corpus = [base_text] + candidate_texts
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            # Наприклад, якщо всі тексти порожні або надто короткі
            return []

        base_vec = tfidf_matrix[0:1]
        other_vecs = tfidf_matrix[1:]

        similarities = cosine_similarity(base_vec, other_vecs)[0]  # shape: (n_candidates,)

        matches: List[Dict[str, Any]] = []
        for idx, sim in enumerate(similarities):
            matches.append(
                {
                    "other_attempt_id": str(candidate_ids[idx]),
                    "similarity_score": float(sim),
                    "match_type": "exact" if sim >= 0.98 else "candidate",
                }
            )

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
            deep_results.append(deep_match)
            max_sim = max(max_sim, semantic_sim)

        deep_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return deep_results, max_sim


    # ---------- ДОПОМІЖНЕ: статус + конвертація в Pydantic ----------

    def _status_from_similarity(self, similarity: float) -> PlagiarismStatus:
        """
        Можеш підкрутити пороги як хочеш.
        """
        if similarity >= 0.9:
            return PlagiarismStatus.high_risk
        if similarity >= 0.7:
            return PlagiarismStatus.suspicious
        return PlagiarismStatus.ok

    def _to_report(self, check) -> PlagiarismReport:
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
