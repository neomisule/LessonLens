from typing import Any

from app.agents.base import BaseAgent


class ConceptAgent(BaseAgent):
    """
    Extracts key concepts from semantic segments using an LLM.

    TODO: Prompt Claude/GPT to identify concepts with definitions,
    explanations, examples, and importance ratings. Persist to the
    `concepts` table and generate concept-level embeddings.
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # Stub — not yet implemented
        return {
            "concepts_ready": False,
            "error": "ConceptAgent not yet implemented",
        }
