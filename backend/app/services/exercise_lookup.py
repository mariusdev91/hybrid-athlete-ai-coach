from typing import Any
from typing import Dict
from typing import List
from typing import Optional

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
        Blended semantic + lexical search with optional filtering.
        """
        normalized_query = normalize_text(query)
        embedding = self.embed_text(normalized_query)
        result_window = max(k * 3, 12)

        semantic_results = vector_store.search(embedding, result_window)
        lexical_results = self._keyword_search(normalized_query, result_window)
        results = self._merge_ranked_results(semantic_results, lexical_results)

        if equipment:
            results = self._filter_by_equipment(results, equipment)

        if primary_muscles:
            results = self._filter_by_primary_muscles(results, primary_muscles)

        if secondary_muscles:
            results = self._filter_by_secondary_muscles(results, secondary_muscles)

        return results[:k]

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

    def _keyword_search(self, normalized_query: str, limit: int) -> List[Dict[str, Any]]:
        query_tokens = [token for token in normalized_query.split(" ") if token]
        if not query_tokens:
            return []

        scored_results = []
        for item in vector_store.metadata:
            score = self._keyword_match_score(item, normalized_query, query_tokens)
            if score <= 0:
                continue
            scored_results.append(
                {
                    **item,
                    "distance": 0.0,
                    "keyword_score": score,
                }
            )

        scored_results.sort(
            key=lambda item: (
                -int(item.get("keyword_score", 0)),
                normalize_text(item.get("name", "")),
            )
        )
        return scored_results[:limit]

    def _keyword_match_score(
        self,
        item: Dict[str, Any],
        normalized_query: str,
        query_tokens: List[str],
    ) -> int:
        name = normalize_text(item.get("name", ""))
        if not name:
            return 0

        score = 0
        if normalized_query and normalized_query in name:
            score += 24

        for token in query_tokens:
            if token in name:
                score += 5

        equipment = normalize_text(item.get("equipment", ""))
        if equipment and equipment in normalized_query:
            score += 3

        primary_muscles = [normalize_text(muscle) for muscle in item.get("primary_muscles", [])]
        secondary_muscles = [normalize_text(muscle) for muscle in item.get("secondary_muscles", [])]
        for token in query_tokens:
            if token in primary_muscles:
                score += 2
            if token in secondary_muscles:
                score += 1

        return score

    def _merge_ranked_results(
        self,
        semantic_results: List[Dict[str, Any]],
        lexical_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}

        for result in semantic_results + lexical_results:
            key = result.get("id") or normalize_text(result.get("name", ""))
            if not key:
                continue

            existing = merged.get(key)
            if existing is None:
                merged[key] = dict(result)
                continue

            candidate_score = int(result.get("keyword_score", 0))
            existing_score = int(existing.get("keyword_score", 0))
            candidate_distance = float(result.get("distance", 999999.0))
            existing_distance = float(existing.get("distance", 999999.0))

            if candidate_score > existing_score or (
                candidate_score == existing_score and candidate_distance < existing_distance
            ):
                merged[key] = {**existing, **result}
            else:
                existing.update(
                    {
                        "keyword_score": max(existing_score, candidate_score),
                        "distance": min(existing_distance, candidate_distance),
                    }
                )

        return sorted(
            merged.values(),
            key=lambda item: (
                -int(item.get("keyword_score", 0)),
                float(item.get("distance", 999999.0)),
            ),
        )


# Singleton instance
exercise_lookup = ExerciseLookupService()
