"""Paraphrase similarity helper.

This module prefers to use the `sentence_transformers` package (and a
pretrained model) for semantic similarity. If the package or model is not
available in the runtime environment (common on CI or when Python/torch
versions are incompatible), the class falls back to a lightweight TF-IDF
cosine-similarity implementation so the application stays functional.
"""

from typing import Optional

try:
    # Prefer the fast neural model when available
    from sentence_transformers import SentenceTransformer, util as _st_util
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SentenceTransformer = None  # type: ignore
    _st_util = None
    _SENTENCE_TRANSFORMERS_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ParaphraseModel:
    """Wrapper providing a .similarity(text1, text2) -> float API.

    - If sentence-transformers is available, use a pretrained model.
    - Otherwise fall back to TF-IDF + cosine similarity (deterministic,
      much cheaper, but less semantically capable).
    """

    def __init__(self, model_name: str = "paraphrase-MiniLM-L6-v2") -> None:
        self._use_nn: bool = False
        self._model_name = model_name
        self._model = None

        if _SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
            try:
                self._model = SentenceTransformer(model_name)
                self._use_nn = True
            except Exception:
                # Model loading failed (e.g. incompatible torch wheel or no
                # network). Fall back to TF-IDF below.
                self._model = None
                self._use_nn = False

        # TF-IDF vectorizer is created on demand for fallback path
        self._vectorizer: Optional[TfidfVectorizer] = None

    def similarity(self, text1: str, text2: str) -> float:
        """Return a similarity score in [0.0, 1.0].

        Returns 0.0 for empty inputs.
        """
        if not text1 or not text2:
            return 0.0

        if self._use_nn and self._model is not None:
            try:
                embeddings = self._model.encode([text1, text2], convert_to_tensor=True)
                cos_sim = float(_st_util.cos_sim(embeddings[0], embeddings[1]).item())
                # Normalize [-1,1] -> [0,1]
                return max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
            except Exception:
                # If runtime NN failure occurs, silently fall back to TF-IDF.
                pass

        # Fallback: TF-IDF + cosine similarity
        try:
            if self._vectorizer is None:
                self._vectorizer = TfidfVectorizer()

            matrix = self._vectorizer.fit_transform([text1, text2])
            vecs = matrix.toarray()
            sim = float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])
            # TF-IDF cosine is already in [0,1] for non-negative vectors
            return max(0.0, min(1.0, sim))
        except Exception:
            # As a last resort, return 0 (no similarity)
            return 0.0
