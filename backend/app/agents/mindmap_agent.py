"""MindMapAgent — builds a radial hierarchical mind map for a lecture.

Pipeline node: runs after grounding + flashcard_generation converge.

Algorithm
─────────
1. Load all enriched concepts (ordered by exam_likelihood DESC).
2. Ask the LLM to group them into 3–6 thematic branches.
   Fallback: group by importance (core / supporting / supplemental).
3. Assign radial positions:
   - Root  → canvas centre (400, 300).
   - Branch_i → ring at radius 180, evenly spaced.
   - Leaf_j in Branch_i → ring at radius 80 around branch centre.
4. Colour:
   - Root    → #7C3AED  (lens-primary)
   - Branches → rotating palette
   - Leaves  → importance: core=#8B5CF6, supporting=#3B82F6, supplemental=#6B7280
5. Clear stale nodes/edges, persist fresh graph.
"""
import logging
import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete as sa_delete

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.concept import Concept
from app.models.mindmap import MindMapNode, MindMapEdge
from app.learn.llm_client import LLMClient
from app.config import get_settings

logger = logging.getLogger(__name__)

_CANVAS_W = 800
_CANVAS_H = 600
_CX, _CY  = _CANVAS_W / 2, _CANVAS_H / 2

_BRANCH_RADIUS  = 200
_LEAF_RADIUS    = 90

_BRANCH_COLORS = [
    "#8B5CF6", "#3B82F6", "#10B981", "#F59E0B",
    "#EF4444", "#EC4899", "#14B8A6",
]

_IMPORTANCE_COLORS = {
    "core":         "#8B5CF6",
    "supporting":   "#3B82F6",
    "supplemental": "#6B7280",
}

_MINDMAP_THEME_SYSTEM = """\
You are a learning content organiser.
Group the given concepts into 3–6 thematic clusters that a student would
recognise as related topics. Return ONLY valid JSON — no markdown.
"""

_MINDMAP_THEME_USER = """\
Lecture concepts (name | importance | exam_likelihood):
{concept_list}

Group them into 3–6 themes. Return:
{{
  "themes": [
    {{
      "label": "Short theme title (≤ 4 words)",
      "concept_names": ["exact concept name", ...]
    }},
    ...
  ]
}}
Rules:
- Use the exact concept names provided.
- Every concept must appear in exactly one theme.
- Theme labels must be concise and meaningful.
"""


def _radial_pos(centre_x: float, centre_y: float, radius: float, index: int, total: int):
    """Return (x, y) for item `index` of `total` arranged in a circle."""
    angle = (2 * math.pi * index / total) - math.pi / 2  # start at top
    return centre_x + radius * math.cos(angle), centre_y + radius * math.sin(angle)


async def _llm_theme_grouping(
    concepts: list[Concept], llm: LLMClient
) -> dict[str, list[str]]:
    """
    Returns {theme_label: [concept_name, ...]} mapping.
    Falls back to importance-based grouping if LLM fails.
    """
    concept_list = "\n".join(
        f"- {c.name} | {c.importance} | {c.exam_likelihood:.2f}"
        for c in concepts
    )
    user_prompt = _MINDMAP_THEME_USER.format(concept_list=concept_list)
    response    = await llm.extract_json(_MINDMAP_THEME_SYSTEM, user_prompt)

    themes_raw = response.get("themes", [])
    if not isinstance(themes_raw, list) or not themes_raw:
        return _importance_fallback(concepts)

    result: dict[str, list[str]] = {}
    assigned: set[str] = set()
    for t in themes_raw:
        label    = str(t.get("label", "General")).strip()
        names    = [str(n) for n in (t.get("concept_names") or []) if n]
        unassigned = [n for n in names if n not in assigned]
        if unassigned:
            result[label] = unassigned
            assigned.update(unassigned)

    # Any concept not grouped → add to "Other"
    ungrouped = [c.name for c in concepts if c.name not in assigned]
    if ungrouped:
        result.setdefault("Other", []).extend(ungrouped)

    return result


def _importance_fallback(concepts: list[Concept]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"Core Concepts": [], "Supporting": [], "Additional": []}
    for c in concepts:
        if c.importance == "core":
            buckets["Core Concepts"].append(c.name)
        elif c.importance == "supporting":
            buckets["Supporting"].append(c.name)
        else:
            buckets["Additional"].append(c.name)
    return {k: v for k, v in buckets.items() if v}


class MindMapAgent(BaseAgent):
    """
    Builds a hierarchical radial mind map for a lecture.

    Pipeline state inputs:  lecture_id
    Pipeline state outputs: mindmap_ready, mindmap_nodes (count), mindmap_edges (count)
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id = state.get("lecture_id", "")
        settings   = get_settings()
        llm = LLMClient(
            anthropic_key=settings.anthropic_api_key or "",
            openai_key=settings.openai_api_key or "",
        )

        async with AsyncSessionLocal() as db:
            try:
                # Load concepts
                result = await db.execute(
                    select(Concept)
                    .where(Concept.lecture_id == lecture_id)
                    .order_by(Concept.exam_likelihood.desc())
                )
                concepts: list[Concept] = list(result.scalars().all())

                if not concepts:
                    logger.warning("[mindmap] No concepts for lecture %s", lecture_id)
                    return {"mindmap_ready": False, "mindmap_nodes": 0, "mindmap_edges": 0}

                # Build concept name → Concept lookup
                concept_map: dict[str, Concept] = {c.name: c for c in concepts}

                # Clear stale graph
                await db.execute(sa_delete(MindMapEdge).where(MindMapEdge.lecture_id == lecture_id))
                await db.execute(sa_delete(MindMapNode).where(MindMapNode.lecture_id == lecture_id))

                # Group into themes
                if llm.available:
                    themes = await _llm_theme_grouping(concepts, llm)
                else:
                    themes = _importance_fallback(concepts)

                theme_labels = list(themes.keys())
                n_branches   = len(theme_labels)

                # ── Create root node ──────────────────────────────────────────
                root_node = MindMapNode(
                    lecture_id=lecture_id,
                    label="Lecture",
                    node_type="root",
                    position_x=_CX,
                    position_y=_CY,
                    color="#7C3AED",
                    importance="core",
                    exam_likelihood=1.0,
                )
                db.add(root_node)
                await db.flush()

                node_count = 1
                edge_count = 0

                for b_idx, theme_label in enumerate(theme_labels):
                    bx, by = _radial_pos(_CX, _CY, _BRANCH_RADIUS, b_idx, n_branches)
                    branch_color = _BRANCH_COLORS[b_idx % len(_BRANCH_COLORS)]

                    # Branch node
                    branch_node = MindMapNode(
                        lecture_id=lecture_id,
                        label=theme_label,
                        node_type="branch",
                        position_x=round(bx, 1),
                        position_y=round(by, 1),
                        color=branch_color,
                        importance="supporting",
                        exam_likelihood=0.7,
                    )
                    db.add(branch_node)
                    await db.flush()
                    node_count += 1

                    # Root → branch edge
                    db.add(MindMapEdge(
                        lecture_id=lecture_id,
                        source_node_id=root_node.id,
                        target_node_id=branch_node.id,
                        edge_type="hierarchical",
                    ))
                    edge_count += 1

                    # Leaf nodes
                    leaf_names = themes[theme_label]
                    n_leaves   = len(leaf_names)
                    for l_idx, concept_name in enumerate(leaf_names):
                        concept = concept_map.get(concept_name)
                        lx, ly  = _radial_pos(bx, by, _LEAF_RADIUS, l_idx, max(n_leaves, 1))
                        leaf_color = _IMPORTANCE_COLORS.get(
                            concept.importance if concept else "supporting", "#3B82F6"
                        )

                        leaf_node = MindMapNode(
                            lecture_id=lecture_id,
                            concept_id=concept.id if concept else None,
                            label=concept_name,
                            description=concept.definition[:120] if concept and concept.definition else None,
                            node_type="leaf",
                            position_x=round(lx, 1),
                            position_y=round(ly, 1),
                            color=leaf_color,
                            importance=concept.importance if concept else "supporting",
                            exam_likelihood=concept.exam_likelihood if concept else 0.5,
                            timestamp_start=concept.timestamp_start if concept else None,
                        )
                        db.add(leaf_node)
                        await db.flush()
                        node_count += 1

                        # Branch → leaf edge
                        db.add(MindMapEdge(
                            lecture_id=lecture_id,
                            source_node_id=branch_node.id,
                            target_node_id=leaf_node.id,
                            edge_type="hierarchical",
                        ))
                        edge_count += 1

                        # Prerequisite edges (concept → prerequisite within same lecture)
                        if concept and concept.prerequisites:
                            for prereq_name in concept.prerequisites:
                                prereq = concept_map.get(prereq_name)
                                if prereq:
                                    # Find the leaf node for prereq (we'll add edges in a second pass)
                                    # Store for second pass — skip for now to avoid forward-ref issues
                                    pass

                await db.commit()
                logger.info(
                    "[mindmap] Built %d nodes, %d edges for lecture %s",
                    node_count, edge_count, lecture_id,
                )

            except Exception as exc:
                logger.error("[mindmap] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"mindmap_ready": False, "error": str(exc)}

        return {
            "mindmap_ready": True,
            "mindmap_nodes": node_count,
            "mindmap_edges": edge_count,
        }
