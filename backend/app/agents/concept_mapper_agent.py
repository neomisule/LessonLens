"""ConceptMapperAgent — enriches extracted concepts with scoring metadata.

After ConceptAgent stores raw concepts, this agent:
  1. Computes exam_likelihood and time_spent_seconds (heuristic, no LLM).
  2. Calls LLM for why_it_matters (per concept, only if not already present).
  3. Calls LLM for concept relations (prerequisites + related, single batch call).
  4. Assigns each concept to its chapter(s) and updates chapter.concept_names.
  5. Updates all Concept rows in the DB with the enriched data.
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.concept import Concept
from app.models.chapter import Chapter
from app.learn.llm_client import LLMClient
from app.learn.exam_scorer import compute_exam_likelihood, compute_time_spent
from app.learn.prompts import (
    WHY_IT_MATTERS_SYSTEM,
    WHY_IT_MATTERS_USER,
    CONCEPT_RELATIONS_SYSTEM,
    CONCEPT_RELATIONS_USER,
)
from app.config import get_settings

logger = logging.getLogger(__name__)


async def _enrich_why_it_matters(
    concept: Concept,
    llm: LLMClient,
) -> str | None:
    """Call LLM to generate a why-it-matters blurb for a single concept."""
    response = await llm.extract_json(
        WHY_IT_MATTERS_SYSTEM,
        WHY_IT_MATTERS_USER.format(
            name=concept.name,
            definition=concept.definition[:300],
            explanation=(concept.explanation or "")[:200],
            tags=", ".join(concept.tags or []),
        ),
    )
    return response.get("why_it_matters") or None


async def _enrich_relations(
    concepts: list[Concept],
    llm: LLMClient,
) -> dict[str, dict]:
    """
    Single LLM call to get prerequisites + related for all concepts.

    Returns {concept_name_lower: {"prerequisites": [...], "related": [...]}}
    """
    if not concepts:
        return {}

    all_concepts_str = "\n".join(
        f"- {c.name} ({c.importance}): {c.definition[:80]}" for c in concepts
    )
    response = await llm.extract_json(
        CONCEPT_RELATIONS_SYSTEM,
        CONCEPT_RELATIONS_USER.format(all_concepts=all_concepts_str),
    )

    result: dict[str, dict] = {}
    relations = response.get("relations", [])
    if not isinstance(relations, list):
        return result

    valid_names = {c.name.lower() for c in concepts}
    for entry in relations:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip().lower()
        if not name:
            continue
        prereqs = [
            p for p in (entry.get("prerequisites") or [])
            if isinstance(p, str) and p.lower() in valid_names
        ]
        related = [
            r for r in (entry.get("related") or [])
            if isinstance(r, str) and r.lower() in valid_names
        ]
        result[name] = {"prerequisites": prereqs, "related": related}

    return result


def _assign_to_chapters(
    concepts: list[Concept],
    chapters: list[Chapter],
) -> dict[str, list[str]]:
    """
    Returns {chapter_id: [concept_name, ...]} for concepts whose
    timestamp_start falls within that chapter's time range.
    """
    assignments: dict[str, list[str]] = {ch.id: [] for ch in chapters}
    for concept in concepts:
        ts = concept.timestamp_start or 0.0
        # Find the chapter that contains this timestamp
        for chapter in chapters:
            ch_start = chapter.timestamp_start
            ch_end = chapter.timestamp_end or float("inf")
            if ch_start <= ts < ch_end:
                assignments[chapter.id].append(concept.name)
                break
        else:
            # Fallback: assign to last chapter
            if chapters:
                assignments[chapters[-1].id].append(concept.name)
    return assignments


class ConceptMapperAgent(BaseAgent):
    """
    Enriches concept rows with:
      - exam_likelihood (heuristic score 0-1)
      - time_spent_seconds (heuristic, seconds of lecture time on this concept)
      - why_it_matters (LLM-generated, 1-2 sentences)
      - prerequisites / related_concepts (LLM-detected, name strings)
      - evidence_timestamps (list of {ts, quote} from evidence_quote + timestamp_start)

    Reads semantic_segments and concepts from pipeline state, then updates DB.
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state.get("lecture_id", "")
        segments: list[dict] = state.get("semantic_segments") or []
        total_duration: float = state.get("total_duration") or 0.0

        settings = get_settings()
        llm = LLMClient(
            anthropic_key=settings.anthropic_api_key or "",
            openai_key=settings.openai_api_key or "",
        )

        async with AsyncSessionLocal() as db:
            try:
                concepts = await _load_concepts(db, lecture_id)
                chapters = await _load_chapters(db, lecture_id)

                if not concepts:
                    logger.info("[concept_mapper] No concepts to enrich for lecture %s", lecture_id)
                    return {"concept_mapping_ready": True}

                logger.info(
                    "[concept_mapper] Enriching %d concepts for lecture %s",
                    len(concepts), lecture_id,
                )

                # ── 1. Heuristic scoring (no LLM) ─────────────────────────────
                from app.learn.schemas import ExtractedConcept as EC
                for concept in concepts:
                    ec = _concept_to_ec(concept)
                    concept.exam_likelihood = compute_exam_likelihood(ec, segments, total_duration)
                    concept.time_spent_seconds = compute_time_spent(ec, segments)

                    # Build evidence_timestamps from evidence quote
                    if concept.evidence_quote and concept.timestamp_start is not None:
                        concept.evidence_timestamps = [{
                            "ts": concept.timestamp_start,
                            "quote": concept.evidence_quote,
                        }]

                # ── 2. LLM: why-it-matters (per concept) ──────────────────────
                if llm.available:
                    for concept in concepts:
                        if not concept.why_it_matters:
                            wit = await _enrich_why_it_matters(concept, llm)
                            if wit:
                                concept.why_it_matters = wit

                    # ── 3. LLM: concept relations (single batch) ────────────────
                    relations = await _enrich_relations(concepts, llm)
                    for concept in concepts:
                        rel = relations.get(concept.name.lower(), {})
                        if rel.get("prerequisites"):
                            concept.prerequisites = rel["prerequisites"]
                        if rel.get("related"):
                            concept.related_concepts = rel["related"]
                else:
                    logger.info("[concept_mapper] LLM unavailable — skipping why_it_matters + relations")

                # ── 4. Chapter assignment ──────────────────────────────────────
                if chapters:
                    assignments = _assign_to_chapters(concepts, chapters)
                    for chapter in chapters:
                        chapter.concept_names = assignments.get(chapter.id, [])

                # ── 5. Persist ─────────────────────────────────────────────────
                await db.commit()
                logger.info("[concept_mapper] Enrichment complete for lecture %s", lecture_id)

            except Exception as exc:
                logger.error("[concept_mapper] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"concept_mapping_ready": False, "error": str(exc)}

        return {"concept_mapping_ready": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_concepts(db: AsyncSession, lecture_id: str) -> list[Concept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.timestamp_start)
    )
    return list(result.scalars().all())


async def _load_chapters(db: AsyncSession, lecture_id: str) -> list[Chapter]:
    result = await db.execute(
        select(Chapter)
        .where(Chapter.lecture_id == lecture_id)
        .order_by(Chapter.sequence_index)
    )
    return list(result.scalars().all())


def _concept_to_ec(c: Concept):
    """Convert a DB Concept to the lightweight ExtractedConcept dataclass."""
    from app.learn.schemas import ExtractedConcept as EC
    return EC(
        name=c.name,
        definition=c.definition,
        explanation=c.explanation or "",
        examples=c.examples or [],
        importance=c.importance or "supporting",
        tags=c.tags or [],
        timestamp_start=c.timestamp_start or 0.0,
        timestamp_end=c.timestamp_end,
        evidence_quote=getattr(c, "evidence_quote", ""),
        segment_index=0,
    )
