import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.routes.admin import router as admin_router
from app.api.routes.database import router as database_router
from app.api.routes.exercises import router as exercises_router
from app.core.exercise_index import bootstrap_vector_store
from app.core.vector_store import vector_store


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    status = bootstrap_vector_store()
    logger.info("Vector store bootstrap: %s", status)
    yield


app = FastAPI(title="Hybrid Athlete AI Coach", lifespan=lifespan)

app.include_router(exercises_router, prefix="/exercises", tags=["Exercises"])
app.include_router(database_router, prefix="/db", tags=["Database"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Hybrid Athlete AI Coach API running",
        "vector_store_ready": vector_store.is_ready,
        "exercise_count": vector_store.count,
    }


@app.get("/test/ai")
def test_ai(query: str):
    from app.services.agent_orchestrator import agent_orchestrator

    return agent_orchestrator.handle_query(query)
