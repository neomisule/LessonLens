from typing import Any

from app.agents.base import BaseAgent


class MindMapAgent(BaseAgent):
    """
    Builds a hierarchical mind map from concepts and their relationships.

    TODO: Ask the LLM to organise concepts into a tree with a root node,
    branch nodes (themes), and leaf nodes (individual concepts). Compute
    initial (x, y) positions using a radial layout algorithm. Persist nodes
    and edges to `mind_map_nodes` / `mind_map_edges`.
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # Stub — not yet implemented
        return {
            "mindmap_ready": False,
            "error": "MindMapAgent not yet implemented",
        }
