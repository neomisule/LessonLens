"""FlashcardAgent — thin pipeline wrapper around ExamCoachAgent.

Registered as the `flashcard_generation` node in the LangGraph pipeline.
All actual generation logic lives in ExamCoachAgent to keep responsibilities
clear: ExamCoachAgent owns flashcard/quiz/mastery generation; this class
simply calls it from the pipeline.
"""
from typing import Any

from app.agents.base import BaseAgent
from app.agents.exam_coach_agent import ExamCoachAgent


class FlashcardAgent(BaseAgent):
    """Pipeline node that delegates to ExamCoachAgent."""

    def __init__(self) -> None:
        self._exam_coach = ExamCoachAgent()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        return await self._exam_coach.run(state)
