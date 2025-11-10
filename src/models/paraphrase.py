from sentence_transformers import SentenceTransformer, util


class ParaphraseModel:
    """
    Обгортка над sentence-transformers моделлю для оцінки схожості двох текстів.
    """

    def __init__(self, model_name: str = "paraphrase-MiniLM-L6-v2") -> None:
        # Модель завантажується один раз при створенні інстансу
        self.model = SentenceTransformer(model_name)

    def similarity(self, text1: str, text2: str) -> float:
        """
        Повертає cosine similarity в діапазоні [0, 1].
        """
        if not text1.strip() or not text2.strip():
            return 0.0

        embeddings = self.model.encode([text1, text2], convert_to_tensor=True)
        cos_sim = util.cos_sim(embeddings[0], embeddings[1]).item()

        # cos_sim ∈ [-1, 1] → нормалізуємо до [0, 1]
        sim_norm = (cos_sim + 1.0) / 2.0
        return max(0.0, min(1.0, sim_norm))
