from functools import lru_cache

from fastapi import APIRouter, Query
from sentence_transformers import SentenceTransformer
from app.core.vector_store import vector_store

router = APIRouter()


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@router.get("/search")
def search_exercise(q: str = Query(..., description="Search query"), k: int = 5):
    embedding = get_embedding_model().encode([q])
    results = vector_store.search(embedding, k)
    return {"query": q, "results": results}
