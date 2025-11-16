from typing import List

class StatisticsService:
    @staticmethod
    def calculate_statistics(scores: List[float]) -> dict:
        """Обчислює мінімум, максимум, медіану та середнє для списку оцінок"""
        if not scores:
            return {"min_score": None, "max_score": None, "median_score": None, "average_score": None}

        min_score = min(scores)
        max_score = max(scores)
        median_score = sorted(scores)[len(scores) // 2]
        average_score = sum(scores) / len(scores)

        return {
            "min_score": min_score,
            "max_score": max_score,
            "median_score": median_score,
            "average_score": average_score
        }
