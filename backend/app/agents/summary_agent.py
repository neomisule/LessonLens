from typing import Any

from app.agents.base import BaseAgent


class SummaryAgent(BaseAgent):
    """
    Produces three-level summaries (brief / standard / detailed) of the lecture.

    TODO: Use map-reduce over semantic segments to generate structured summaries
    with section headings and timestamps. Persist all three variants to the
    `summaries` table so the frontend can switch between them without re-calling.
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # Stub — not yet implemented
        return {
            "summaries_ready": False,
            "error": "SummaryAgent not yet implemented",
        }
