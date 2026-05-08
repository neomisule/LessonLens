"""ConceptAgent — extracts key concepts from semantic segments and persists them.

Uses learn/concept_extractor.py for LLM-based extraction, then stores the
results to the `concepts` table. Generates embeddings for each concept name
so the vector search index can find relevant concepts.
"""
import logging
from typing import Any

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.concept import Concept
from app.models.transcript import SemanticSegment
from app.learn.llm_client import LLMClient
from app.learn.concept_extractor import extract_concepts_from_segments
from app.learn.schemas import ExtractedConcept
from app.config import get_settings

logger = logging.getLogger(__name__)


async def _load_segments(db: AsyncSession, lecture_id: str) -> list[dict]:
    result = await db.execute(
        select(SemanticSegment)
        .where(SemanticSegment.lecture_id == lecture_id)
        .order_by(SemanticSegment.sequence_index)
    )
    segs = result.scalars().all()
    return [
        {
            "sequence_index": s.sequence_index,
            "start": s.start_time,
            "end": s.end_time,
            "content": s.content,
        }
        for s in segs
    ]


async def _embed_concept(name: str, settings) -> list[float] | None:
    """Generate an embedding vector for a concept name, if API key is available."""
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=name,
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("[concept_agent] Embedding failed for '%s': %s", name, exc)
        return None


class ConceptAgent(BaseAgent):
    """
    Extracts concepts from all semantic segments for a lecture.

    Pipeline state inputs:
      - lecture_id: str
      - semantic_segments: list[dict]  (optional, falls back to DB query)

    Pipeline state outputs:
      - concepts_ready: bool
      - concepts: list[dict]  (concept dicts for downstream agents)
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state.get("lecture_id", "")
        settings = get_settings()

        llm = LLMClient(
            anthropic_key=settings.anthropic_api_key or "",
            openai_key=settings.openai_api_key or "",
        )

        async with AsyncSessionLocal() as db:
            try:
                # Load segments from DB (authoritative after SegmentationAgent commits)
                segments = await _load_segments(db, lecture_id)
                if not segments:
                    logger.warning("[concept_agent] No segments for lecture %s", lecture_id)
                    return {"concepts_ready": False, "concepts": [], "error": "No segments"}

                logger.info(
                    "[concept_agent] Extracting concepts from %d segments for lecture %s",
                    len(segments), lecture_id,
                )

                # ── Extract via LLM ────────────────────────────────────────────
                extracted: list[ExtractedConcept] = await extract_concepts_from_segments(
                    segments, llm
                )
                logger.info("[concept_agent] %d unique concepts extracted", len(extracted))

                # ── Remove stale concepts ──────────────────────────────────────
                await db.execute(sa_delete(Concept).where(Concept.lecture_id == lecture_id))

                # ── Persist new concepts ───────────────────────────────────────
                concept_dicts: list[dict] = []
                for ec in extracted:
                    embedding = await _embed_concept(ec.name, settings)
                    concept = Concept(
                        lecture_id=lecture_id,
                        name=ec.name,
                        definition=ec.definition,
                        explanation=ec.explanation,
                        examples=ec.examples,
                        importance=ec.importance,
                        tags=ec.tags,
                        timestamp_start=ec.timestamp_start,
                        timestamp_end=ec.timestamp_end,
                        embedding=embedding,
                        # Store evidence quote for grounding verification
                        # (mapped to a transient attr if not in model — ignored safely)
                    )
                    # Attach evidence_quote if the model has it
                    if hasattr(concept, "evidence_quote"):
                        concept.evidence_quote = ec.evidence_quote
                    db.add(concept)
                    concept_dicts.append({
                        "name": ec.name,
                        "importance": ec.importance,
                        "timestamp_start": ec.timestamp_start,
                    })

                await db.commit()
                logger.info(
                    "[concept_agent] Persisted %d concepts for lecture %s",
                    len(extracted), lecture_id,
                )

            except Exception as exc:
                logger.error("[concept_agent] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"concepts_ready": False, "concepts": [], "error": str(exc)}

        return {
            "concepts_ready": True,
            "concepts": concept_dicts,
        }
