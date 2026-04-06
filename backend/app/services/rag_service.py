from typing import Dict, Any, List, Optional
from app.services.exercise_lookup import exercise_lookup
from app.utils.normalizer import normalize_text


class RAGService:
    """
    High-level retrieval layer for the AI Coach.
    Decides what type of retrieval to perform based on the query.
    """

    def retrieve_context(
        self,
        query: str,
        equipment: Optional[str] = None,
        primary_muscles: Optional[List[str]] = None,
        secondary_muscles: Optional[List[str]] = None,
        k: int = 8,
    ) -> Dict[str, Any]:
        """
        Main entry point for agents.
        Returns structured context based on the query.
        """

        normalized_query = normalize_text(query)

        # For now, all queries go through exercise search.
        # Later we can add: nutrition, recovery, mobility, etc.
        exercises = exercise_lookup.search_exercises(
            query=normalized_query,
            equipment=equipment,
            primary_muscles=primary_muscles,
            secondary_muscles=secondary_muscles,
            k=k,
        )

        return {
            "query": query,
            "normalized_query": normalized_query,
            "results": exercises,
            "count": len(exercises),
        }

    def retrieve_alternatives(self, exercise_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Returns similar exercises for substitution.
        """
        return exercise_lookup.find_alternatives(exercise_id, k)


# Singleton instance
rag_service = RAGService()
