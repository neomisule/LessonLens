"""Service layer for Break It Down Mode.

Wires together:
  - ConfusionRescueAgent (LLM explanation generation + caching)
  - VoiceAgent (ElevenLabs TTS + audio caching)
  - Revisit recommendation logic (heuristic, no LLM)
"""
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.concept import Concept
from app.models.explanation_cache import ExplanationCache
from app.learn.llm_client import LLMClient
from app.breakdown.elevenlabs_client import ElevenLabsClient
from app.breakdown.schemas import (
    ExplanationStyle,
    ExplanationResult,
    AudioResult,
    RevisitRecommendation,
    SUPPORTED_LANGUAGES,
)
from app.agents.confusion_rescue_agent import ConfusionRescueAgent
from app.agents.voice_agent import VoiceAgent
from app.schemas.breakdown import (
    ExplanationRead,
    AudioRead,
    RevisitRecommendationRead,
)

logger = logging.getLogger(__name__)

# ── Singleton agents (one per process) ───────────────────────────────────────
# Built lazily so we don't instantiate at import time

_rescue_agent: ConfusionRescueAgent | None = None
_voice_agent: VoiceAgent | None = None


def _get_rescue_agent() -> ConfusionRescueAgent:
    global _rescue_agent
    if _rescue_agent is None:
        settings = get_settings()
        llm = LLMClient(
            anthropic_key=settings.anthropic_api_key,
            openai_key=settings.openai_api_key,
        )
        _rescue_agent = ConfusionRescueAgent(llm)
    return _rescue_agent


def _get_voice_agent() -> VoiceAgent:
    global _voice_agent
    if _voice_agent is None:
        settings = get_settings()
        storage = Path(settings.audio_storage_path)
        el_client = ElevenLabsClient(
            api_key=settings.elevenlabs_api_key,
            storage_path=storage,
        )
        _voice_agent = VoiceAgent(el_client, storage)
    return _voice_agent


# ── Explanation generation ────────────────────────────────────────────────────

async def get_or_create_explanation(
    db: AsyncSession,
    concept_id: str,
    style: ExplanationStyle,
    language: str,
) -> ExplanationRead | None:
    """Generate (or retrieve cached) explanation. Returns None on failure."""
    agent = _get_rescue_agent()
    result: ExplanationResult | None = await agent.explain(
        db, concept_id, style, language
    )
    if not result:
        return None

    # Fetch the persisted row for the full ExplanationRead
    cached_row = await db.execute(
        select(ExplanationCache).where(
            ExplanationCache.concept_id == concept_id,
            ExplanationCache.style == style.value,
            ExplanationCache.language == language,
        )
    )
    row = cached_row.scalar_one_or_none()
    if not row:
        return None

    audio_url = None
    if row.audio_cache_key:
        audio_url = f"/api/v1/breakdown/audio/{row.id}"

    return ExplanationRead(
        id=row.id,
        concept_id=row.concept_id,
        style=row.style,
        language=row.language,
        content=row.content,
        source_quote=row.source_quote,
        timestamp_start=row.timestamp_start,
        audio_url=audio_url,
        audio_duration_ms=row.audio_duration_ms,
        cached=result.cached,
        generated_at=row.generated_at,
    )


async def list_cached_explanations(
    db: AsyncSession,
    concept_id: str,
) -> list[ExplanationRead]:
    """Return all cached explanations for a concept."""
    result = await db.execute(
        select(ExplanationCache)
        .where(ExplanationCache.concept_id == concept_id)
        .order_by(ExplanationCache.generated_at.desc())
    )
    rows = result.scalars().all()
    out = []
    for row in rows:
        audio_url = f"/api/v1/breakdown/audio/{row.id}" if row.audio_cache_key else None
        out.append(ExplanationRead(
            id=row.id,
            concept_id=row.concept_id,
            style=row.style,
            language=row.language,
            content=row.content,
            source_quote=row.source_quote,
            timestamp_start=row.timestamp_start,
            audio_url=audio_url,
            audio_duration_ms=row.audio_duration_ms,
            cached=True,
            generated_at=row.generated_at,
        ))
    return out


# ── Audio generation ──────────────────────────────────────────────────────────

async def generate_audio(
    db: AsyncSession,
    explanation_id: str,
) -> AudioRead:
    """Generate TTS audio for an explanation. Returns AudioRead with URL."""
    agent = _get_voice_agent()
    result: AudioResult = await agent.generate(db, explanation_id)
    return AudioRead(
        explanation_id=result.explanation_id,
        audio_url=result.audio_url,
        duration_ms=result.duration_ms,
        cached=result.cached,
        error=result.error,
    )


def get_audio_path(explanation_cache_key: str) -> Path | None:
    """Return the on-disk Path for a given audio cache key."""
    return _get_voice_agent().get_audio_path(explanation_cache_key)


# ── Revisit recommendations ────────────────────────────────────────────────────

async def get_revisit_recommendations(
    db: AsyncSession,
    lecture_id: str,
    limit: int = 5,
) -> list[RevisitRecommendationRead]:
    """
    Heuristic revisit recommendations — no LLM needed.

    Ranks concepts by:
    1. Core importance + high exam_likelihood → must revisit
    2. Has prerequisites (foundational to other concepts)
    3. Introduced early in the lecture (foundational)
    4. Low time_spent_seconds relative to exam_likelihood (under-explored)
    """
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.timestamp_start)
    )
    concepts = list(result.scalars().all())

    scored: list[tuple[float, Concept, str]] = []
    for c in concepts:
        reason, score = _score_concept_for_revisit(c, concepts)
        if score > 0:
            scored.append((score, c, reason))

    scored.sort(key=lambda x: -x[0])
    top = scored[:limit]

    return [
        RevisitRecommendationRead(
            concept_id=c.id,
            concept_name=c.name,
            reason=reason,
            priority=i + 1,
            timestamp_start=c.timestamp_start,
            exam_likelihood=c.exam_likelihood,
            importance=c.importance,
        )
        for i, (_, c, reason) in enumerate(top)
    ]


def _score_concept_for_revisit(
    concept: Concept,
    all_concepts: list[Concept],
) -> tuple[str, float]:
    """Return (reason_string, priority_score) for a concept."""
    score = 0.0
    reasons = []

    # High exam likelihood
    if concept.exam_likelihood >= 0.75:
        score += 3.0
        reasons.append("High exam likelihood")
    elif concept.exam_likelihood >= 0.5:
        score += 1.5
        reasons.append("Moderate exam likelihood")

    # Core concepts
    if concept.importance == "core":
        score += 2.0
        if "core" not in " ".join(reasons).lower():
            reasons.append("Core concept")

    # Is a prerequisite of another concept
    names_that_need_it = [
        c.name for c in all_concepts
        if concept.name in (c.prerequisites or [])
    ]
    if names_that_need_it:
        score += 1.5
        reasons.append(f"Prerequisite for {names_that_need_it[0]}")

    # Under-explored (short time spent relative to exam likelihood)
    time_s = concept.time_spent_seconds or 0.0
    if time_s < 30 and concept.exam_likelihood > 0.4:
        score += 1.0
        reasons.append("Covered briefly")

    if not reasons:
        return "", 0.0

    return reasons[0], round(score, 2)
