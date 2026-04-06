from fastapi import APIRouter
from fastapi import HTTPException

from app.core.exercise_index import rebuild_vector_store
from app.core.vector_store import vector_store

router = APIRouter()


@router.get("/vector-store/status")
def vector_store_status():
    return {
        "ready": vector_store.is_ready,
        "count": vector_store.count,
    }


@router.post("/vector-store/rebuild")
def rebuild_vector_store_endpoint():
    try:
        count = rebuild_vector_store(persist=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector store rebuild failed: {exc}") from exc

    return {
        "status": "ok",
        "count": count,
    }
