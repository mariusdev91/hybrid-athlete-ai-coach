from fastapi import APIRouter
import json
from sentence_transformers import SentenceTransformer
from app.core.vector_store import vector_store
from app.utils.normalizer import normalize_text

router = APIRouter()

MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@router.post("/build-vector-store")
def build_vector_store():
    """
    Loads exercises.json and rebuilds the FAISS vector index.
    """
    try:
        with open("app/data/exercises.json", "r") as f:
            exercises = json.load(f)
    except Exception as e:
        return {"error": f"Cannot load exercises.json: {e}"}

    vector_store.index.reset()
    vector_store.metadata = []

    for ex in exercises:
        text = f"{ex['name']} {ex.get('primary_muscles', [])} {ex.get('equipment', '')}"
        text = normalize_text(text)
        embedding = MODEL.encode(text).tolist()
        vector_store.add(embedding, ex)

    return {
        "status": "ok",
        "count": len(vector_store.metadata)
    }
