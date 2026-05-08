from typing import Any

from app.agents.base import BaseAgent


class FlashcardAgent(BaseAgent):
    """
    Generates Anki-style flashcards from extracted concepts.

    TODO: For each concept, ask the LLM to produce front/back pairs
    with difficulty tags and topic labels. Persist to `flashcards`
    table. Initialize `user_mastery` rows at "unseen".
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # Stub — not yet implemented
        return {
            "flashcards_ready": False,
            "error": "FlashcardAgent not yet implemented",
        }
