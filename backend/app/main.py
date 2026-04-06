from fastapi import FastAPI
from app.api.routes.exercises import router as exercises_router

app = FastAPI(title="Hybrid Athlete AI Coach")

app.include_router(exercises_router, prefix="/exercises", tags=["Exercises"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Hybrid Athlete AI Coach API running"}
