from typing import List, Optional, Dict, Any

from app.core.exercise_index import get_embedding_model
from app.core.vector_store import vector_store
from app.utils.normalizer import normalize_text


class ExerciseLookupService:
    """
    High-level interface for searching and filtering exercises.
    Combines semantic search (FAISS) with logical filtering.
    """

    def embed_text(self, text: str):
        """
        Generate a 384-dim embedding for FAISS.
        """
        if not text:
            return [0.0] * 384

        embedding = get_embedding_model().encode(text)
        return embedding.tolist()

    def search_exercises(
        self,
        query: str,
        equipment: Optional[str] = None,
        primary_muscles: Optional[List[str]] = None,
        secondary_muscles: Optional[List[str]] = None,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search + optional filtering.
        """
        normalized_query = normalize_text(query)
        embedding = self.embed_text(normalized_query)

        results = vector_store.search(embedding, k)

        # Apply filters
        if equipment:
            results = self._filter_by_equipment(results, equipment)

        if primary_muscles:
            results = self._filter_by_primary_muscles(results, primary_muscles)

        if secondary_muscles:
            results = self._filter_by_secondary_muscles(results, secondary_muscles)

        return results

    def find_alternatives(self, exercise_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Finds similar exercises based on the name of the exercise.
        """
        exercise = self._find_by_id(exercise_id)
        if not exercise:
            return []

        query = exercise["name"]
        embedding = self.embed_text(query)
        results = vector_store.search(embedding, k + 1)

        # Remove the original exercise from results
        return [r for r in results if r["id"] != exercise_id][:k]

    # -------------------------
    # Internal helper functions
    # -------------------------

    def _find_by_id(self, exercise_id: str):
        for item in vector_store.metadata:
            if item["id"] == exercise_id:
                return item
        return None

    def _filter_by_equipment(self, results, equipment):
        equipment = equipment.lower()
        return [
            r for r in results
            if r.get("equipment") and equipment in r["equipment"].lower()
        ]

    def _filter_by_primary_muscles(self, results, muscles):
        muscles = {m.lower() for m in muscles}
        return [
            r for r in results
            if any(m.lower() in muscles for m in r.get("primary_muscles", []))
        ]

    def _filter_by_secondary_muscles(self, results, muscles):
        muscles = {m.lower() for m in muscles}
        return [
            r for r in results
            if any(m.lower() in muscles for m in r.get("secondary_muscles", []))
        ]


# Singleton instance
exercise_lookup = ExerciseLookupService()
