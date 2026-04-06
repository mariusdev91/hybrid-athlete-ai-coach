from typing import Dict, Any
from app.services.rag_service import rag_service
from app.agents.exercise_agent import ExerciseAgent
from app.agents.workout_agent import WorkoutAgent
from app.agents.coach_agent import CoachAgent


class AgentOrchestrator:
    """
    Routes user queries to the correct agent and injects RAG context.
    """

    def __init__(self):
        self.exercise_agent = ExerciseAgent()
        self.workout_agent = WorkoutAgent()
        self.coach_agent = CoachAgent()

    def handle_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for the AI Coach.
        """

        # Decide which agent should handle the query
        agent = self._select_agent(query)

        # Retrieve context from RAG
        context = rag_service.retrieve_context(query)

        # Let the agent generate the final answer
        response = agent.generate_response(query, context)

        return {
            "query": query,
            "agent": agent.name,
            "context_used": context,
            "response": response,
        }

    def _select_agent(self, query: str):
        """
        Simple rule-based agent selection.
        Later we can replace with LLM-based routing.
        """
        q = query.lower()

        if any(word in q for word in ["exercise", "glutes", "stretch", "mobility", "pain"]):
            return self.exercise_agent

        if any(word in q for word in ["workout", "program", "routine", "plan"]):
            return self.workout_agent

        return self.coach_agent


# Singleton
agent_orchestrator = AgentOrchestrator()
