"""Break It Down Mode API router.

Endpoints:
  POST   /breakdown/explain            → generate/retrieve explanation
  GET    /breakdown/{concept_id}/explanations → list cached explanations
  POST   /breakdown/audio              → generate TTS for explanation
  GET    /breakdown/audio/{explanation_id}    → stream MP3 file
  GET    /breakdown/{lecture_id}/revisit      → revisit recommendations
  GET    /breakdown/languages          → list supported languages
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.explanation_cache import ExplanationCache
from app.breakdown.schemas import ExplanationStyle, SUPPORTED_LANGUAGES
from app.schemas.breakdown import (
    ExplainRequest,
    AudioRequest,
    ExplanationRead,
    AudioRead,
    RevisitRecommendationRead,
    SupportedLanguagesRead,
)
import app.services.breakdown_service as svc

router = APIRouter(prefix="/breakdown", tags=["breakdown"])


# ── Languages ─────────────────────────────────────────────────────────────────

@router.get("/languages", response_model=SupportedLanguagesRead)
async def get_languages():
    """Return all languages supported by the TTS engine."""
    return SupportedLanguagesRead(languages=SUPPORTED_LANGUAGES)


# ── Explanation ───────────────────────────────────────────────────────────────

@router.post("/explain", response_model=ExplanationRead)
async def explain(
    payload: ExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate (or retrieve cached) an alternative explanation.

    The style and language combination is cached permanently —
    subsequent identical requests return instantly from the DB.
    """
    lang = payload.validated_language()
    result = await svc.get_or_create_explanation(
        db,
        concept_id=payload.concept_id,
        style=payload.style,
        language=lang,
    )
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Unable to generate explanation. LLM may be unavailable.",
        )
    return result


@router.get("/{concept_id}/explanations", response_model=list[ExplanationRead])
async def list_explanations(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all previously generated explanations for a concept."""
    return await svc.list_cached_explanations(db, concept_id)


# ── Audio ─────────────────────────────────────────────────────────────────────

@router.post("/audio", response_model=AudioRead)
async def generate_audio(
    payload: AudioRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate TTS audio for a stored explanation.

    First call triggers ElevenLabs API (≈1-3s). Subsequent calls return
    instantly from the on-disk cache.
    """
    result = await svc.generate_audio(db, payload.explanation_id)
    if result.error and not result.audio_url:
        raise HTTPException(status_code=503, detail=result.error)
    return result


@router.get("/audio/{explanation_id}")
async def stream_audio(
    explanation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream the MP3 file for a generated explanation."""
    # Load the cache key from DB
    result = await db.execute(
        select(ExplanationCache).where(ExplanationCache.id == explanation_id)
    )
    row = result.scalar_one_or_none()
    if not row or not row.audio_cache_key:
        raise HTTPException(status_code=404, detail="Audio not generated yet")

    path = svc.get_audio_path(row.audio_cache_key)
    if path is None:
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        path=str(path),
        media_type="audio/mpeg",
        filename=f"explanation_{explanation_id[:8]}.mp3",
    )


# ── Revisit recommendations ───────────────────────────────────────────────────

@router.get("/{lecture_id}/revisit", response_model=list[RevisitRecommendationRead])
async def get_revisit(
    lecture_id: str,
    limit: int = Query(default=5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Return heuristic revisit recommendations for a lecture."""
    return await svc.get_revisit_recommendations(db, lecture_id, limit=limit)
