from fastapi import FastAPI
from app.routers import chat, exercises, agents

app = FastAPI(
    title="Hybrid Athlete AI Coach",
    version="0.1.0",
    description="AI Coach with multi-agent system + RAG + exercise DB"
)

# Register routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(exercises.router, prefix="/exercises", tags=["Exercises"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])

@app.get("/")
def root():
    return {"message": "Hybrid Athlete AI Coach API is running"}
