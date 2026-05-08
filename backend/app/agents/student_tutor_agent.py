"""StudentTutorAgent — orchestrates all Learn Mode generation tasks.

Responsibilities:
  1. Detect and persist lecture chapters (ChapterDetector).
  2. Generate and persist all three summary levels (SummaryGenerator).
  3. Persist a lean TotalDuration value to the pipeline state for downstream
     agents (ConceptMapperAgent reads it from state).

This agent runs AFTER SegmentationAgent and ConceptAgent, and BEFORE
ConceptMapperAgent and GroundingAgent.

It never generates any content not grounded in the provided transcript — all LLM
calls pass the actual segment text as context and enforce the grounding rules
defined in app/learn/prompts.py.
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.summary import Summary
from app.models.chapter import Chapter
from app.models.concept import Concept
from app.models.transcript import SemanticSegment
from app.models.lecture import Lecture
from app.learn.llm_client import LLMClient
from app.learn.chapter_detector import detect_chapters
from app.learn.summary_generator import generate_all_summaries
from app.learn.schemas import ExtractedConcept, GeneratedSummary, SummarySection
from app.config import get_settings

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_semantic_segments(db: AsyncSession, lecture_id: str) -> list[dict]:
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
            "topic_boundary_score": s.topic_boundary_score or 1.0,
        }
        for s in segs
    ]


async def _load_concepts_as_ec(db: AsyncSession, lecture_id: str) -> list[ExtractedConcept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.timestamp_start)
    )
    concepts = result.scalars().all()
    return [
        ExtractedConcept(
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
        for c in concepts
    ]


async def _get_lecture_title(db: AsyncSession, lecture_id: str) -> str:
    result = await db.execute(
        select(Lecture.title).where(Lecture.id == lecture_id)
    )
    row = result.scalar_one_or_none()
    return str(row) if row else "Lecture"


def _section_to_dict(s: SummarySection) -> dict:
    return {
        "heading": s.heading,
        "content": s.content,
        "timestamp_start": s.timestamp_start,
        "timestamp_end": s.timestamp_end,
        "key_points": s.key_points,
    }


async def _persist_chapters(
    db: AsyncSession,
    lecture_id: str,
    chapters_data,
) -> None:
    """Delete old chapters and insert fresh ones."""
    # Remove stale chapters
    from sqlalchemy import delete as sa_delete
    await db.execute(sa_delete(Chapter).where(Chapter.lecture_id == lecture_id))

    for ch in chapters_data:
        db.add(Chapter(
            lecture_id=lecture_id,
            sequence_index=ch.sequence_index,
            title=ch.title,
            summary=ch.summary or None,
            timestamp_start=ch.timestamp_start,
            timestamp_end=ch.timestamp_end,
            concept_names=ch.concept_names,
        ))


async def _persist_summaries(
    db: AsyncSession,
    lecture_id: str,
    summaries: list[GeneratedSummary],
) -> None:
    """Upsert summaries — replace existing level rows."""
    from sqlalchemy import delete as sa_delete
    for gs in summaries:
        # Remove old summary at this level if it exists
        await db.execute(
            sa_delete(Summary).where(
                Summary.lecture_id == lecture_id,
                Summary.level == gs.level,
            )
        )
        sections_json = [_section_to_dict(s) for s in gs.sections]
        db.add(Summary(
            lecture_id=lecture_id,
            level=gs.level,
            title=gs.title,
            content=gs.content,
            sections=sections_json,
        ))


# ── Agent ─────────────────────────────────────────────────────────────────────

class StudentTutorAgent(BaseAgent):
    """
    Orchestrates Learn Mode content generation:
      - Chapter detection via ChapterDetector
      - Three-level summary generation via SummaryGenerator

    Reads semantic segments from DB (not state) for reliability after
    SegmentationAgent has committed them.

    Output state keys:
      - learn_ready: bool
      - total_duration: float   (seconds of the lecture)
      - chapters_count: int
      - summaries_count: int
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
                segments = await _load_semantic_segments(db, lecture_id)
                if not segments:
                    logger.warning("[student_tutor] No segments for lecture %s", lecture_id)
                    return {
                        "learn_ready": False,
                        "error": "No semantic segments available",
                    }

                total_duration = segments[-1].get("end", 0.0) if segments else 0.0
                title = await _get_lecture_title(db, lecture_id)
                concepts = await _load_concepts_as_ec(db, lecture_id)

                logger.info(
                    "[student_tutor] lecture=%s | segments=%d | concepts=%d | duration=%.0fs",
                    lecture_id, len(segments), len(concepts), total_duration,
                )

                # ── 1. Chapter detection ───────────────────────────────────────
                chapters = await detect_chapters(segments, llm, total_duration)
                logger.info("[student_tutor] %d chapters detected", len(chapters))
                await _persist_chapters(db, lecture_id, chapters)

                # ── 2. Summary generation ──────────────────────────────────────
                summaries = await generate_all_summaries(
                    segments=segments,
                    concepts=concepts,
                    lecture_title=title,
                    total_duration=total_duration,
                    llm=llm,
                )
                logger.info("[student_tutor] %d summary levels generated", len(summaries))
                await _persist_summaries(db, lecture_id, summaries)

                await db.commit()

            except Exception as exc:
                logger.error("[student_tutor] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"learn_ready": False, "error": str(exc)}

        return {
            "learn_ready": True,
            "total_duration": total_duration,
            "chapters_count": len(chapters),
            "summaries_count": len(summaries),
        }
