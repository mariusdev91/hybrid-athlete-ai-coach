from fastapi import APIRouter
from app.services.agent_orchestrator import orchestrate_chat

router = APIRouter()

@router.post("/")
async def chat_endpoint(message: str):
    response = await orchestrate_chat(message)
    return {"response": response}
