"""TranscriptAgent — LangGraph node for transcript extraction.

Responsibilities:
  1. Report "downloading" progress (fetch metadata, update lecture row)
  2. Report "transcribing" progress (IngestionAgent fetches + normalises)
  3. Persist TranscriptSegment rows and TranscriptQuality row to the DB
  4. Return ingested segment dicts for downstream SegmentationAgent

State keys consumed : lecture_id, job_id, youtube_url, youtube_id
State keys produced : transcript_ready, transcript_segments, transcript_quality,
                      transcript_error (on failure)
"""
import logging
from typing import Any

from sqlalchemy import select

from app.agents.base import BaseAgent
from app.agents.ingestion_agent import IngestionAgent, InsufficientTranscriptError
from app.config import get_settings
from app.database import async_session_factory
from app.models.lecture import Lecture
from app.models.transcript import TranscriptSegment
from app.models.transcript_quality import TranscriptQuality
from app.transcript.progress import ProgressReporter

logger = logging.getLogger(__name__)


class TranscriptAgent(BaseAgent):
    """LangGraph node: fetch, normalise, score, and store transcript."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._ingestion = IngestionAgent(self._settings)

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state["lecture_id"]
        job_id: str = state["job_id"]
        youtube_url: str = state["youtube_url"]
        youtube_id: str = state.get("youtube_id", "")

        reporter = ProgressReporter(job_id)

        # ── Step 1: downloading (metadata fetch) ──────────────────────────────
        await reporter.set_step("downloading")

        try:
            result = await self._ingestion.ingest(
                lecture_id=lecture_id,
                youtube_url=youtube_url,
                youtube_id=youtube_id,
            )
        except InsufficientTranscriptError as exc:
            logger.error("[transcript_agent] Insufficient transcript: %s", exc)
            await reporter.fail(str(exc))
            return {
                "transcript_ready": False,
                "transcript_error": str(exc),
                "error": str(exc),
            }
        except Exception as exc:
            logger.exception("[transcript_agent] Unexpected error")
            await reporter.fail(f"Transcript extraction failed: {exc}")
            return {
                "transcript_ready": False,
                "transcript_error": str(exc),
                "error": str(exc),
            }

        meta = result.metadata
        quality = result.quality
        segments = result.segments

        await reporter.complete_step("downloading", detail={
            "title": meta.title,
            "channel": meta.channel_name,
            "method": quality.method,
        })

        # ── Step 2: transcribing → persist to DB ──────────────────────────────
        await reporter.set_step("transcribing", detail={
            "method": quality.method,
            "is_fallback": quality.method == "whisper_fallback",
        })

        async with async_session_factory() as db:
            # Update lecture metadata
            lecture: Lecture | None = await db.get(Lecture, lecture_id)
            if lecture:
                lecture.title = meta.title
                lecture.channel_name = meta.channel_name
                lecture.thumbnail_url = meta.thumbnail_url
                if quality.total_duration > 0:
                    lecture.duration_seconds = int(quality.total_duration)

            # Clear any stale transcript rows
            existing = await db.execute(
                select(TranscriptSegment).where(TranscriptSegment.lecture_id == lecture_id)
            )
            for old_seg in existing.scalars().all():
                await db.delete(old_seg)

            # Insert new TranscriptSegment rows
            db_segments: list[TranscriptSegment] = []
            for idx, seg in enumerate(segments):
                db_seg = TranscriptSegment(
                    lecture_id=lecture_id,
                    sequence_index=idx,
                    content=seg.text,
                    timestamp_start=seg.start,
                    timestamp_end=seg.end,
                    source=quality.method,
                    confidence=seg.confidence,
                )
                db.add(db_seg)
                db_segments.append(db_seg)

            # Upsert TranscriptQuality
            existing_q = await db.execute(
                select(TranscriptQuality).where(TranscriptQuality.lecture_id == lecture_id)
            )
            tq = existing_q.scalar_one_or_none()
            gap_locations = [[g.start, g.end] for g in quality.gaps]

            if tq:
                tq.method = quality.method
                tq.is_fallback = quality.method == "whisper_fallback"
                tq.confidence_avg = quality.confidence_avg
                tq.confidence_min = quality.confidence_min
                tq.noise_ratio = quality.noise_ratio
                tq.coverage_pct = quality.coverage_pct
                tq.gap_count = quality.gap_count
                tq.gap_locations = gap_locations
                tq.word_count = quality.word_count
                tq.segment_count = quality.segment_count
                tq.total_duration = quality.total_duration
            else:
                tq = TranscriptQuality(
                    lecture_id=lecture_id,
                    method=quality.method,
                    is_fallback=quality.method == "whisper_fallback",
                    confidence_avg=quality.confidence_avg,
                    confidence_min=quality.confidence_min,
                    noise_ratio=quality.noise_ratio,
                    coverage_pct=quality.coverage_pct,
                    gap_count=quality.gap_count,
                    gap_locations=gap_locations,
                    word_count=quality.word_count,
                    segment_count=quality.segment_count,
                    total_duration=quality.total_duration,
                )
                db.add(tq)

            await db.commit()

        await reporter.complete_step("transcribing", detail={
            "segment_count": quality.segment_count,
            "word_count": quality.word_count,
            "coverage_pct": quality.coverage_pct,
            "confidence_avg": quality.confidence_avg,
            "gap_count": quality.gap_count,
            "is_fallback": quality.method == "whisper_fallback",
        })

        # Serialise segments for pipeline state (avoid passing ORM objects)
        transcript_segments = [
            {
                "sequence_index": idx,
                "content": seg.text,
                "start": seg.start,
                "end": seg.end,
                "confidence": seg.confidence,
                "source": quality.method,
            }
            for idx, seg in enumerate(segments)
        ]

        return {
            "transcript_ready": True,
            "transcript_segments": transcript_segments,
            "transcript_quality": {
                "method": quality.method,
                "confidence_avg": quality.confidence_avg,
                "coverage_pct": quality.coverage_pct,
                "word_count": quality.word_count,
                "gap_count": quality.gap_count,
            },
        }
