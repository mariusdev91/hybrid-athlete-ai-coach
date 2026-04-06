from fastapi import APIRouter
from app.services.exercise_lookup import search_exercises

router = APIRouter()

@router.get("/search")
async def search(q: str):
    results = search_exercises(q)
    return {"results": results}
