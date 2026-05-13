"""IngestionAgent — coordinates YouTube metadata + transcript fetching.

This class is a pure orchestrator with NO database access and NO LangGraph
coupling — it only fetches, normalises, and scores data.  Database writes
are handled by the TranscriptAgent LangGraph node.

Design goals
------------
- Never hallucinate content: if no captions exist and fallback fails, raise.
- Return IngestionResult that includes quality metadata for storage.
- Be synchronous-compatible: caption fetching runs synchronously (youtube_transcript_api
  has no async interface), metadata is async via httpx.
"""
import asyncio
import logging

from app.transcript.schemas import IngestionResult, NormalizedSegment, RawSegment
from app.transcript.youtube_client import fetch_video_metadata, fetch_captions_sync
from app.transcript.normalizer import normalize_segments, merge_short_segments
from app.transcript.quality_scorer import score_quality

logger = logging.getLogger(__name__)


class IngestionAgent:
    """
    Orchestrates the full ingestion flow for one YouTube lecture.

    Usage::

        agent = IngestionAgent(settings)
        result = await agent.ingest(
            lecture_id="...",
            youtube_url="https://www.youtube.com/watch?v=...",
            youtube_id="dQw4w9WgXcQ",
        )

    The returned IngestionResult contains:
    - metadata  : VideoMetadata (title, channel, thumbnail)
    - segments  : list[NormalizedSegment]  (ready for DB storage)
    - quality   : QualityReport  (method, confidence, coverage, …)
    """

    def __init__(self, settings) -> None:
        self._settings = settings

    async def ingest(
        self,
        lecture_id: str,
        youtube_url: str,
        youtube_id: str,
    ) -> IngestionResult:
        """
        Full ingestion pipeline.

        1. Fetch video metadata (oEmbed, async)
        2. Fetch YouTube captions (sync, thread)
        3. Normalise + merge segments
        4. Score quality
        5. If quality is poor, attempt Whisper fallback
        6. If fallback also fails, raise InsufficientTranscriptError

        Raises
        ------
        InsufficientTranscriptError
            When no usable transcript could be obtained by any method.
        """
        # ── 1+2. Metadata + captions in parallel ─────────────────────────────
        logger.info("[ingestion] Fetching metadata + captions in parallel for %s", youtube_id)
        loop = asyncio.get_running_loop()
        metadata, raw_segs = await asyncio.gather(
            fetch_video_metadata(youtube_id),
            loop.run_in_executor(None, fetch_captions_sync, youtube_id),
        )
        raw_segs: list[RawSegment] | None = raw_segs

        method = "youtube_captions"
        segments: list[NormalizedSegment] = []

        if raw_segs:
            segments = merge_short_segments(normalize_segments(raw_segs))
            # Estimate total duration from last segment
            total_dur = raw_segs[-1].start + raw_segs[-1].duration if raw_segs else 0.0
            quality = score_quality(segments, total_dur, method=method)
        else:
            quality = None

        # ── 3. Fallback chain (only if captions missing/poor) ─────────────────
        if quality is None or quality.is_poor:
            logger.info(
                "[ingestion] Quality is %s for %s — trying fallback chain",
                "absent" if quality is None else "poor",
                youtube_id,
            )

            # Fast fallback: yt-dlp subtitle download (~3s, no API key needed)
            from app.transcript.fallback_stt import download_subtitles_ytdlp
            ytdlp_segs = await download_subtitles_ytdlp(youtube_url)
            if ytdlp_segs:
                method = "ytdlp_subtitles"
                segments = merge_short_segments(normalize_segments(ytdlp_segs))
                total_dur = ytdlp_segs[-1].start + ytdlp_segs[-1].duration
                quality = score_quality(segments, total_dur, method=method)
                quality.is_poor = False
                logger.info("[ingestion] yt-dlp subtitles succeeded: %d segments", len(segments))

        if quality is None or quality.is_poor:
            # Slow fallback: full audio download + Whisper (needs GROQ_API_KEY or OPENAI_API_KEY)
            fallback_segs = await self._try_whisper_fallback(youtube_url)

            if fallback_segs:
                method = "whisper_fallback"
                segments = merge_short_segments(normalize_segments(fallback_segs))
                total_dur = fallback_segs[-1].start + fallback_segs[-1].duration if fallback_segs else 0.0
                quality = score_quality(segments, total_dur, method=method)
                quality.is_poor = False

        # ── 4. Validate we have something ─────────────────────────────────────
        if not segments:
            raise InsufficientTranscriptError(
                f"No transcript could be obtained for {youtube_id}. "
                "YouTube captions are disabled and Whisper fallback failed."
            )

        if quality is None:
            # Shouldn't happen, but be safe
            total_dur = segments[-1].end if segments else 0.0
            quality = score_quality(segments, total_dur, method=method)

        quality.method = method

        logger.info(
            "[ingestion] Complete — %d segments, coverage=%.1f%%, method=%s",
            quality.segment_count, quality.coverage_pct, method,
        )

        return IngestionResult(metadata=metadata, segments=segments, quality=quality)

    async def _try_whisper_fallback(
        self,
        youtube_url: str,
    ) -> list[RawSegment] | None:
        """Attempt Whisper fallback; tries Groq first (fast), then OpenAI."""
        groq_key = getattr(self._settings, "groq_api_key", "") or ""
        openai_key = self._settings.openai_api_key or ""

        if not groq_key and not openai_key:
            logger.warning("[ingestion] Whisper fallback skipped: no STT API key configured")
            return None

        from app.transcript.fallback_stt import transcribe_fallback
        return await transcribe_fallback(
            youtube_url,
            groq_api_key=groq_key,
            openai_api_key=openai_key,
        )


class InsufficientTranscriptError(RuntimeError):
    """Raised when no usable transcript exists for a lecture."""
