from fastapi import APIRouter, Query
from app.core.exercise_index import get_embedding_model
from app.core.vector_store import vector_store

router = APIRouter()


@router.get("/search")
def search_exercise(q: str = Query(..., description="Search query"), k: int = 5):
    embedding = get_embedding_model().encode([q])
    results = vector_store.search(embedding, k)
    return {
        "query": q,
        "results": results,
        "count": len(results),
        "vector_store_ready": vector_store.is_ready,
    }
