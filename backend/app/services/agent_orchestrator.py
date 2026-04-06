async def orchestrate_chat(message: str):
    # TODO: orchestrator logic + agents
    return f"Received: {message}"

def list_agents():
    return [
        "exercise_agent",
        "strength_agent",
        "conditioning_agent",
        "sport_specific_agent",
        "load_management_agent"
    ]
