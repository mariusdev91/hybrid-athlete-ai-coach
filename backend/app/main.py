from fastapi import FastAPI
from app.api.routes.database import router as database_router
from app.api.routes.exercises import router as exercises_router

app = FastAPI(title="Hybrid Athlete AI Coach")

app.include_router(exercises_router, prefix="/exercises", tags=["Exercises"])
app.include_router(database_router, prefix="/db", tags=["Database"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Hybrid Athlete AI Coach API running"}

@app.get("/test/ai")
def test_ai(query: str):
    from app.services.agent_orchestrator import agent_orchestrator

    return agent_orchestrator.handle_query(query)
