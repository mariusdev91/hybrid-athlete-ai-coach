from fastapi import APIRouter
from app.services.agent_orchestrator import list_agents

router = APIRouter()

@router.get("/")
def get_agents():
    return {"agents": list_agents()}
