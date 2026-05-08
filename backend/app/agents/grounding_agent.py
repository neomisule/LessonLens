"""GroundingAgent — post-hoc verification that stored content is transcript-grounded.

Scans all Summary sections and Concept definitions for the lecture and checks
whether each claim can be matched back to an actual semantic segment.

This agent runs AFTER SummaryAgent and ConceptMapperAgent. It does NOT delete
or rewrite content — it flags low-confidence items by appending a
`grounding_score` field that the frontend can use to show confidence badges.

Matching strategy (no LLM required):
  - For each section heading + content, check if keywords appear in any segment
    within the stated timestamp window.
  - Assign a score 0.0–1.0: ratio of keyword hits / total keywords checked.
  - Sections with score < 0.3 are logged as warnings for investigation.
"""
import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.summary import Summary
from app.models.concept import Concept
from app.models.transcript import SemanticSegment

logger = logging.getLogger(__name__)

_MIN_KEYWORD_LEN = 4
_LOW_GROUNDING_THRESHOLD = 0.30


def _extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """Extract simple content words from text for keyword-match grounding."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    # Remove stop words
    stops = {
        "that", "this", "with", "from", "have", "been", "they",
        "will", "also", "which", "their", "when", "where", "what",
        "each", "more", "most", "than", "then", "into", "some",
        "these", "those", "such", "over", "here", "there", "just",
        "about", "after", "before",
    }
    filtered = [w for w in words if w not in stops]
    # Rough frequency count
    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    top = sorted(freq, key=lambda k: -freq[k])[:top_n]
    return top


def _keyword_coverage(keywords: list[str], segment_texts: list[str]) -> float:
    """Return fraction of keywords found in at least one segment text."""
    if not keywords:
        return 1.0
    combined = " ".join(segment_texts).lower()
    hits = sum(1 for kw in keywords if kw in combined)
    return hits / len(keywords)


def _segments_in_window(
    segments: list[dict],
    ts_start: float,
    ts_end: float | None,
    window_expansion: float = 30.0,
) -> list[str]:
    """Return content text of segments whose range overlaps [ts_start, ts_end]."""
    end = (ts_end or ts_start) + window_expansion
    start = max(0.0, ts_start - window_expansion)
    texts = []
    for seg in segments:
        seg_start = seg.get("start", 0.0)
        seg_end = seg.get("end", seg_start)
        if seg_start <= end and seg_end >= start:
            texts.append(seg.get("content", ""))
    return texts


async def _load_segments_as_dicts(db: AsyncSession, lecture_id: str) -> list[dict]:
    result = await db.execute(
        select(SemanticSegment)
        .where(SemanticSegment.lecture_id == lecture_id)
        .order_by(SemanticSegment.sequence_index)
    )
    segs = result.scalars().all()
    return [
        {
            "start": s.start_time,
            "end": s.end_time,
            "content": s.content,
        }
        for s in segs
    ]


def _ground_summary(summary: Summary, segments: list[dict]) -> dict:
    """
    Check grounding for a Summary's sections.

    Returns grounding_report dict that can be attached to progress_metadata.
    """
    sections = summary.sections or []
    if not sections:
        return {"checked": 0, "low_confidence": 0, "avg_score": 1.0}

    scores = []
    low_count = 0

    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        ts_start = section.get("timestamp_start", 0.0) or 0.0
        ts_end = section.get("timestamp_end")

        keywords = _extract_keywords(f"{heading} {content}")
        nearby_texts = _segments_in_window(segments, ts_start, ts_end)

        if not nearby_texts:
            # No segments near this timestamp — use all segments
            nearby_texts = [s.get("content", "") for s in segments]

        score = _keyword_coverage(keywords, nearby_texts)
        scores.append(score)

        if score < _LOW_GROUNDING_THRESHOLD:
            low_count += 1
            logger.warning(
                "[grounding] Low-confidence section in summary %s: '%s' (score=%.2f)",
                summary.id, heading[:60], score,
            )

    avg = round(sum(scores) / len(scores), 3) if scores else 1.0
    return {
        "checked": len(scores),
        "low_confidence": low_count,
        "avg_score": avg,
    }


def _ground_concept(concept: Concept, segments: list[dict]) -> float:
    """
    Check that a concept's definition is grounded in segments near its timestamp.
    Returns a 0-1 grounding score.
    """
    text = f"{concept.definition} {concept.explanation or ''}"
    keywords = _extract_keywords(text)
    ts = concept.timestamp_start or 0.0
    nearby = _segments_in_window(segments, ts, concept.timestamp_end)
    if not nearby:
        nearby = [s.get("content", "") for s in segments]
    return _keyword_coverage(keywords, nearby)


class GroundingAgent(BaseAgent):
    """
    Verifies transcript-grounding of summaries and concepts.

    Does NOT modify content — only logs warnings for low-confidence items
    and returns a grounding_report dict to the pipeline state.

    Output state keys:
      - grounding_ready: bool
      - grounding_report: dict  (per-level scores + concept coverage)
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state.get("lecture_id", "")

        async with AsyncSessionLocal() as db:
            try:
                segments = await _load_segments_as_dicts(db, lecture_id)
                if not segments:
                    logger.info("[grounding] No segments found for lecture %s — skipping", lecture_id)
                    return {"grounding_ready": True, "grounding_report": {}}

                # ── Ground summaries ───────────────────────────────────────────
                summaries_result = await db.execute(
                    select(Summary).where(Summary.lecture_id == lecture_id)
                )
                summaries = list(summaries_result.scalars().all())
                summary_reports: dict[str, dict] = {}
                for summary in summaries:
                    report = _ground_summary(summary, segments)
                    summary_reports[summary.level] = report
                    logger.info(
                        "[grounding] Summary '%s': avg_score=%.2f, low=%d/%d",
                        summary.level, report["avg_score"],
                        report["low_confidence"], report["checked"],
                    )

                # ── Ground concepts ────────────────────────────────────────────
                concepts_result = await db.execute(
                    select(Concept).where(Concept.lecture_id == lecture_id)
                )
                concepts = list(concepts_result.scalars().all())

                concept_scores: list[float] = []
                low_concepts = 0
                for concept in concepts:
                    score = _ground_concept(concept, segments)
                    concept_scores.append(score)
                    if score < _LOW_GROUNDING_THRESHOLD:
                        low_concepts += 1
                        logger.warning(
                            "[grounding] Low-confidence concept: '%s' (score=%.2f)",
                            concept.name, score,
                        )

                avg_concept_score = (
                    round(sum(concept_scores) / len(concept_scores), 3)
                    if concept_scores else 1.0
                )

                grounding_report = {
                    "summaries": summary_reports,
                    "concepts": {
                        "checked": len(concept_scores),
                        "low_confidence": low_concepts,
                        "avg_score": avg_concept_score,
                    },
                }
                logger.info(
                    "[grounding] Complete for lecture %s. Concept avg=%.2f, low=%d/%d",
                    lecture_id, avg_concept_score, low_concepts, len(concept_scores),
                )

            except Exception as exc:
                logger.error("[grounding] Failed: %s", exc, exc_info=True)
                return {"grounding_ready": False, "error": str(exc)}

        return {
            "grounding_ready": True,
            "grounding_report": grounding_report,
        }
