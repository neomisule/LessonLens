from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all LangGraph pipeline agents."""

    @abstractmethod
    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's work on the pipeline state.

        Args:
            state: The current LangGraph pipeline state dict.

        Returns:
            A partial state dict with the keys this agent sets/updates.
        """
        ...

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Make agents callable as LangGraph nodes."""
        return await self.run(state)
