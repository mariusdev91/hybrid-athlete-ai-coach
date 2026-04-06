from fastapi import APIRouter, Query
from sentence_transformers import SentenceTransformer
from app.core.vector_store import vector_store

router = APIRouter()
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@router.get("/search")
def search_exercise(q: str = Query(..., description="Search query"), k: int = 5):
    embedding = model.encode([q])
    results = vector_store.search(embedding, k)
    return {"query": q, "results": results}
