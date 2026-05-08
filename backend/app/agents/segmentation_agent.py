"""SegmentationAgent — LangGraph node for semantic chunking.

Responsibilities:
  1. Read TranscriptSegment dicts from pipeline state
  2. Group into 15-second TranscriptChunks
  3. Generate embeddings for each chunk (batch call to OpenAI)
  4. Detect topic boundaries via cosine similarity
  5. Persist SemanticSegment rows with embeddings to the DB
  6. Mark "segmenting" step complete

State keys consumed : transcript_ready, transcript_segments, lecture_id, job_id
State keys produced : segmentation_ready, semantic_segments
"""
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.config import get_settings
from app.database import async_session_factory
from app.models.transcript import NormalizedSegment as ORMSegment, SemanticSegment
from app.transcript.schemas import NormalizedSegment, TranscriptChunk
from app.transcript.chunker import chunk_into_windows
from app.transcript.segmenter import (
    detect_topic_boundaries,
    build_semantic_segments,
    fallback_fixed_segments,
)
from app.transcript.progress import ProgressReporter

logger = logging.getLogger(__name__)


class SegmentationAgent(BaseAgent):
    """LangGraph node: chunk → embed → topic-segment → store."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        if not state.get("transcript_ready"):
            # Propagate upstream failure without adding noise
            return {
                "segmentation_ready": False,
                "error": state.get("error", "Transcript not ready; skipping segmentation"),
            }

        lecture_id: str = state["lecture_id"]
        job_id: str = state["job_id"]
        raw_segments: list[dict] = state.get("transcript_segments", [])

        reporter = ProgressReporter(job_id)
        await reporter.set_step("segmenting")

        # ── 1. Reconstruct NormalizedSegment objects ──────────────────────────
        norm_segments: list[NormalizedSegment] = [
            NormalizedSegment(
                text=s["content"],
                start=s["start"],
                end=s["end"],
                timestamp_str=self._fmt(s["start"]),
                confidence=s.get("confidence", 0.85),
                is_noise=False,
            )
            for s in raw_segments
        ]

        # ── 2. Chunk into 15-second windows ───────────────────────────────────
        chunks: list[TranscriptChunk] = chunk_into_windows(norm_segments)
        logger.info("[segmentation] %d 15-s chunks from %d segments", len(chunks), len(norm_segments))

        if not chunks:
            await reporter.fail("No transcript chunks produced; cannot segment.")
            return {
                "segmentation_ready": False,
                "error": "No chunks produced from transcript",
            }

        # ── 3. Generate embeddings (batch) ────────────────────────────────────
        embeddings: list[list[float]] | None = None
        if self._settings.openai_api_key:
            try:
                from app.vector.store import create_embeddings_batch
                chunk_texts = [c.text for c in chunks]
                embeddings = await create_embeddings_batch(chunk_texts)
                logger.info("[segmentation] Got %d embeddings", len(embeddings))
            except Exception as exc:
                logger.warning("[segmentation] Embedding failed, using fixed segmentation: %s", exc)
                embeddings = None
        else:
            logger.info("[segmentation] No OpenAI key; using fixed-window segmentation")

        # ── 4. Topic boundary detection ───────────────────────────────────────
        if embeddings and len(embeddings) == len(chunks):
            boundary_indices = detect_topic_boundaries(embeddings)
            seg_dicts = build_semantic_segments(chunks, boundary_indices, embeddings)
        else:
            seg_dicts = fallback_fixed_segments(chunks)

        logger.info("[segmentation] %d semantic segments produced", len(seg_dicts))

        # ── 5. Persist SemanticSegments with embeddings ───────────────────────
        # Map chunk index → embedding for segment-level embedding (use first chunk's embedding)
        chunk_embed_map: dict[int, list[list[float]]] = {}
        if embeddings:
            # Build map from chunk start time → embedding index
            start_to_idx = {c.start: i for i, c in enumerate(chunks)}
            chunk_embed_map = start_to_idx  # type: ignore[assignment]

        async with async_session_factory() as db:
            # Delete stale semantic segments for this lecture
            from sqlalchemy import select, delete
            await db.execute(
                delete(SemanticSegment).where(SemanticSegment.lecture_id == lecture_id)
            )

            for seg_dict in seg_dicts:
                # Find the embedding for the first chunk in this segment
                seg_embedding: list[float] | None = None
                if embeddings:
                    # Find chunk index whose start matches segment start
                    for ci, chunk in enumerate(chunks):
                        if abs(chunk.start - seg_dict["start"]) < 0.1:
                            seg_embedding = embeddings[ci]
                            break

                db_seg = SemanticSegment(
                    lecture_id=lecture_id,
                    sequence_index=seg_dict["sequence_index"],
                    content=seg_dict["content"],
                    timestamp_start=seg_dict["start"],
                    timestamp_end=seg_dict["end"],
                    embedding=seg_embedding,
                    token_count=seg_dict["token_count"],
                    topic_boundary_score=seg_dict["topic_boundary_score"],
                )
                db.add(db_seg)

            await db.commit()

        await reporter.complete_step("segmenting", detail={
            "chunk_count": len(chunks),
            "segment_count": len(seg_dicts),
            "embeddings_generated": embeddings is not None,
        })

        return {
            "segmentation_ready": True,
            "semantic_segments": seg_dicts,
        }

    @staticmethod
    def _fmt(seconds: float) -> str:
        """Quick MM:SS formatter (avoids importing normalizer)."""
        total = max(0, int(seconds))
        m, s = divmod(total, 60)
        return f"{m}:{s:02d}"
