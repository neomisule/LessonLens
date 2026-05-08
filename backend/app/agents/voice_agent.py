"""VoiceAgent — generates TTS audio for explanation text via ElevenLabs.

Responsibilities:
  1. Check ExplanationCache for audio_cache_key — if set, the file already
     exists on disk (or can be regenerated from the same key).
  2. Call ElevenLabsClient.generate_audio() — which handles its own
     disk-level cache by SHA-256 key.
  3. Update ExplanationCache.audio_cache_key + audio_duration_ms.
  4. Return AudioResult with the relative URL path for streaming.

The audio URL served to the frontend is:
  GET /api/v1/breakdown/audio/{explanation_id}
which streams the MP3 file from disk.
"""
import hashlib
import logging
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.explanation_cache import ExplanationCache
from app.breakdown.elevenlabs_client import ElevenLabsClient
from app.breakdown.schemas import AudioResult

logger = logging.getLogger(__name__)


def _audio_cache_key(text: str, voice_id: str, model_id: str) -> str:
    """Mirrors ElevenLabsClient._cache_key for pre-check."""
    payload = f"{model_id}:{voice_id}:{text}"
    return hashlib.sha256(payload.encode()).hexdigest()


class VoiceAgent:
    """
    Orchestrates audio generation for a stored explanation.

    Usage::
        agent = VoiceAgent(elevenlabs_client, storage_path)
        result = await agent.generate(db, explanation_id)
    """

    def __init__(
        self,
        client: ElevenLabsClient,
        storage_path: Path,
    ) -> None:
        self._client = client
        self._storage = storage_path

    async def generate(
        self,
        db: AsyncSession,
        explanation_id: str,
    ) -> AudioResult:
        """
        Generate or return cached audio for an ExplanationCache row.

        Returns AudioResult with audio_url set to:
          /api/v1/breakdown/audio/{explanation_id}
        The streaming endpoint reads from disk using the explanation's
        audio_cache_key to locate the MP3 file.
        """
        # ── Load explanation ──────────────────────────────────────────────────
        result = await db.execute(
            select(ExplanationCache).where(ExplanationCache.id == explanation_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return AudioResult(
                explanation_id=explanation_id,
                audio_url="",
                duration_ms=None,
                error="Explanation not found",
            )

        # ── Already has audio ─────────────────────────────────────────────────
        if row.audio_cache_key:
            key = row.audio_cache_key
            audio_path = self._storage / key[:2] / f"{key}.mp3"
            if audio_path.exists():
                logger.debug("[voice_agent] Cache HIT for explanation %s", explanation_id[:8])
                return AudioResult(
                    explanation_id=explanation_id,
                    audio_url=f"/api/v1/breakdown/audio/{explanation_id}",
                    duration_ms=row.audio_duration_ms,
                    cached=True,
                )

        # ── ElevenLabs not configured ─────────────────────────────────────────
        if not self._client.available:
            return AudioResult(
                explanation_id=explanation_id,
                audio_url="",
                duration_ms=None,
                error="Audio generation not configured",
            )

        # ── Generate audio ────────────────────────────────────────────────────
        audio_path, duration_ms, from_cache = await self._client.generate_audio(
            text=row.content,
        )

        if audio_path is None:
            return AudioResult(
                explanation_id=explanation_id,
                audio_url="",
                duration_ms=None,
                error="Audio generation failed",
            )

        # ── Update DB row with cache key ──────────────────────────────────────
        # Derive the key from the path stem (the key IS the stem)
        key = audio_path.stem
        row.audio_cache_key = key
        row.audio_duration_ms = duration_ms
        await db.commit()

        logger.info(
            "[voice_agent] Audio ready for explanation %s (cached=%s)",
            explanation_id[:8], from_cache,
        )

        return AudioResult(
            explanation_id=explanation_id,
            audio_url=f"/api/v1/breakdown/audio/{explanation_id}",
            duration_ms=duration_ms,
            cached=from_cache,
        )

    def get_audio_path(self, cache_key: str) -> Path | None:
        """Return the on-disk path for a given audio_cache_key, or None."""
        path = self._storage / cache_key[:2] / f"{cache_key}.mp3"
        return path if path.exists() else None
