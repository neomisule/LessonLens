"""Staged processing pipeline.

Architecture:
  ┌─ transcript_extracting ──────────────────────────────────────────────────┐
  │  Download captions / Whisper fallback. Cache: skip if segments exist.    │
  └─ segmenting ─────────────────────────────────────────────────────────────┘
  ┌─ extracting_concepts ────────────────────────────────────────────────────┐
  │  BATCH: ceil(N_segs/4) LLM calls instead of N_segs calls.               │
  └──────────────────────────────────────────────────────────────────────────┘
  ┌─ Fast path  (parallel asyncio.gather) ───────────────────────────────────┐
  │  chapters_brief_summary  │  initial_flashcards (top-8, 1 batch call)    │
  └──────────────────── dashboard_ready ─────────────────────────────────────┘
  ┌─ Deep path (parallel, failure-isolated) ─────────────────────────────────┐
  │  concept_enrichment  │  deep_summaries  │  full_flashcards_quiz          │
  └──────────────────────────────────────────────────────────────────────────┘
  ┌─ mindmap ─ complete ─────────────────────────────────────────────────────┘

LLM call count comparison (20-min lecture, ~10 segments, ~20 concepts):
  Old pipeline:  ~120 sequential calls  (~10 min minimum, often 2+ hrs with backoff)
  New pipeline:  ~8  calls total        (fast path ~45s, deep path ~30s more)
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.jobs.worker import celery_app
from app.database import async_session_factory
from app.models.lecture import Lecture
from app.models.processing import ProcessingJob
from app.models.transcript import SemanticSegment, TranscriptSegment

logger = logging.getLogger(__name__)


# ── Stage timer ───────────────────────────────────────────────────────────────

class StageTimer:
    """Tracks wall-clock time for named stages and produces a log summary."""

    def __init__(self) -> None:
        self._starts: dict[str, float] = {}
        self._log:    list[dict]       = []

    def start(self, name: str) -> None:
        self._starts[name] = time.perf_counter()

    def stop(
        self,
        name:      str,
        llm_calls: int  = 0,
        success:   bool = True,
        detail:    str  = "",
    ) -> float:
        t0 = self._starts.pop(name, time.perf_counter())
        duration = time.perf_counter() - t0
        entry = {
            "stage":      name,
            "duration_s": round(duration, 2),
            "llm_calls":  llm_calls,
            "success":    success,
            "detail":     detail,
        }
        self._log.append(entry)
        logger.info(
            "[timing] %-30s  %.2fs  llm=%d  ok=%s  %s",
            name, duration, llm_calls, success, detail,
        )
        return duration

    def summary(self) -> list[dict]:
        return list(self._log)


# ── Job / lecture DB helpers ──────────────────────────────────────────────────

async def _update_job(
    job_id:      str,
    status:      str  | None = None,
    step:        str  | None = None,
    error:       str  | None = None,
    stage_error: tuple[str, str] | None = None,
    meta:        dict | None = None,
) -> None:
    async with async_session_factory() as db:
        job: ProcessingJob | None = await db.get(ProcessingJob, job_id)
        if not job:
            return
        if status:
            job.status = status
        if step is not None:
            job.current_step = step
        if error:
            job.error_message = error
        if stage_error:
            errs = dict(job.stage_errors or {})
            errs[stage_error[0]] = stage_error[1]
            job.stage_errors = errs
        if meta:
            existing = dict(job.progress_metadata or {})
            existing.update(meta)
            job.progress_metadata = existing
        if status in ("complete", "failed"):
            job.completed_at = datetime.now()
        await db.commit()


async def _mark_step_done(job_id: str, step: str) -> None:
    async with async_session_factory() as db:
        job: ProcessingJob | None = await db.get(ProcessingJob, job_id)
        if not job:
            return
        completed = list(job.steps_completed or [])
        if step not in completed:
            completed.append(step)
        job.steps_completed = completed
        await db.commit()


async def _finish_lecture(lecture_id: str, status: str, error: str | None = None) -> None:
    async with async_session_factory() as db:
        lecture = await db.get(Lecture, lecture_id)
        if lecture:
            lecture.processing_status = status
            if status == "completed":
                lecture.processed_at = datetime.now()
            if error:
                lecture.processing_error = error
            await db.commit()


# ── Cache checks ──────────────────────────────────────────────────────────────

async def _has_transcript_rows(lecture_id: str) -> bool:
    """True if raw transcript segments exist (skip extraction on re-runs)."""
    async with async_session_factory() as db:
        row = (await db.execute(
            select(TranscriptSegment.id)
            .where(TranscriptSegment.lecture_id == lecture_id)
            .limit(1)
        )).scalar_one_or_none()
        return row is not None


async def _has_semantic_segments(lecture_id: str) -> bool:
    """True if semantic segments exist (skip segmentation on re-runs)."""
    async with async_session_factory() as db:
        row = (await db.execute(
            select(SemanticSegment.id)
            .where(SemanticSegment.lecture_id == lecture_id)
            .limit(1)
        )).scalar_one_or_none()
        return row is not None


# ── Isolated stage runner ─────────────────────────────────────────────────────

async def _run_isolated(
    stage: str,
    job_id: str,
    timer: StageTimer,
    coro,
    *,
    hard: bool = False,
) -> tuple[bool, Any]:
    """
    Run a coroutine with per-stage error isolation.

    Returns (success, result).
    - On failure, records the error in the job row and logs it.
    - If hard=True, re-raises (used for stages that make everything downstream impossible).
    - Failures in non-hard stages are stored in stage_errors so the frontend
      can show which sections are unavailable without failing the whole job.
    """
    await _update_job(job_id, step=stage)
    timer.start(stage)
    try:
        result = await coro
        timer.stop(stage, success=True)
        await _mark_step_done(job_id, stage)
        return True, result
    except Exception as exc:
        msg = str(exc)
        timer.stop(stage, success=False, detail=msg[:120])
        logger.error("[pipeline] stage=%s FAILED: %s", stage, msg, exc_info=True)
        await _update_job(job_id, stage_error=(stage, msg[:500]))
        if hard:
            raise
        return False, None


# ── Per-stage async coroutines ────────────────────────────────────────────────

async def _do_transcript(
    lecture_id: str, job_id: str, youtube_url: str, youtube_id: str
) -> dict:
    from app.agents.transcript_agent import TranscriptAgent
    return await TranscriptAgent().run({
        "lecture_id": lecture_id, "job_id": job_id,
        "youtube_url": youtube_url, "youtube_id": youtube_id,
    })


async def _do_segmentation(lecture_id: str, job_id: str) -> dict:
    from app.agents.segmentation_agent import SegmentationAgent
    return await SegmentationAgent().run({"lecture_id": lecture_id, "job_id": job_id})


async def _do_concepts(lecture_id: str, job_id: str) -> dict:
    from app.agents.concept_agent import ConceptAgent
    return await ConceptAgent().run({"lecture_id": lecture_id, "job_id": job_id})


async def _do_chapters_brief_summary(lecture_id: str, job_id: str) -> dict:
    """Fast path: chapters + brief summary only (1 LLM call each)."""
    from app.agents.student_tutor_agent import StudentTutorAgent
    return await StudentTutorAgent().run({
        "lecture_id": lecture_id,
        "job_id": job_id,
        "summary_levels": ["brief"],
    })


async def _do_initial_flashcards(lecture_id: str, job_id: str) -> dict:
    """Fast path: top-8 concepts, 1 surface card each, 1 batch LLM call."""
    from app.agents.exam_coach_agent import ExamCoachAgent
    return await ExamCoachAgent().run({
        "lecture_id": lecture_id,
        "job_id": job_id,
        "fast_path": True,
    })


async def _do_concept_enrichment(
    lecture_id: str, job_id: str, total_duration: float
) -> dict:
    """Background: why-it-matters + relations for all concepts (1 batch call)."""
    from app.agents.concept_mapper_agent import ConceptMapperAgent
    return await ConceptMapperAgent().run({
        "lecture_id": lecture_id,
        "job_id": job_id,
        "total_duration": total_duration,
    })


async def _do_deep_summaries(lecture_id: str, job_id: str) -> dict:
    """Background: standard + detailed summaries (2 LLM calls)."""
    from app.agents.student_tutor_agent import StudentTutorAgent
    return await StudentTutorAgent().run({
        "lecture_id": lecture_id,
        "job_id": job_id,
        "summary_levels": ["standard", "detailed"],
    })


async def _do_full_flashcards_and_quiz(lecture_id: str, job_id: str) -> dict:
    """Background: full flashcard set + quiz questions via batch calls."""
    from app.agents.exam_coach_agent import ExamCoachAgent
    return await ExamCoachAgent().run({
        "lecture_id": lecture_id,
        "job_id": job_id,
        "fast_path": False,
    })


async def _do_mindmap(lecture_id: str, job_id: str) -> dict:
    from app.agents.mindmap_agent import MindMapAgent
    return await MindMapAgent().run({"lecture_id": lecture_id, "job_id": job_id})


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def _run_pipeline(lecture_id: str, job_id: str) -> None:
    timer = StageTimer()

    # Load lecture metadata
    async with async_session_factory() as db:
        lecture: Lecture | None = await db.get(Lecture, lecture_id)
        if not lecture:
            logger.error("[pipeline] Lecture %s not found", lecture_id)
            return
        youtube_url = lecture.youtube_url
        youtube_id  = lecture.youtube_id

    await _update_job(
        job_id,
        status="processing",
        step="transcript_extracting",
        meta={"pipeline_start": datetime.now().isoformat()},
    )

    # ── Stage 1: Transcript ───────────────────────────────────────────────────
    if await _has_transcript_rows(lecture_id):
        logger.info("[pipeline] %s: transcript cached — skipping extraction", lecture_id)
        await _mark_step_done(job_id, "transcript_extracting")
        timer.start("transcript_extracting")
        timer.stop("transcript_extracting", detail="cached")
    else:
        await _run_isolated(
            "transcript_extracting", job_id, timer,
            _do_transcript(lecture_id, job_id, youtube_url, youtube_id),
            hard=True,
        )

    # ── Stage 2: Segmentation ─────────────────────────────────────────────────
    if await _has_semantic_segments(lecture_id):
        logger.info("[pipeline] %s: segments cached — skipping segmentation", lecture_id)
        await _mark_step_done(job_id, "segmenting")
        timer.start("segmenting")
        timer.stop("segmenting", detail="cached")
    else:
        await _run_isolated(
            "segmenting", job_id, timer,
            _do_segmentation(lecture_id, job_id),
            hard=True,
        )

    await _update_job(job_id, status="transcript_ready", step="extracting_concepts")

    # ── Stage 3+4a: Concept extraction ∥ chapters (overlap saves ~10-15s) ────
    # chapters_brief_summary only needs semantic segments (already in DB).
    # initial_flashcards needs concepts → starts after concepts are done.
    await _update_job(job_id, status="fast_materials_generating", step="fast_materials_generating")

    gather_results = await asyncio.gather(
        _run_isolated(
            "extracting_concepts", job_id, timer,
            _do_concepts(lecture_id, job_id),
        ),
        _run_isolated(
            "chapters_brief_summary", job_id, timer,
            _do_chapters_brief_summary(lecture_id, job_id),
        ),
    )

    # Extract total_duration from the tutor result for downstream stages
    _, tutor_result = gather_results[1]
    total_duration: float = (tutor_result or {}).get("total_duration", 0.0)

    # ── Stage 4b: Initial flashcards (needs concepts, now available) ─────────
    await _run_isolated(
        "initial_flashcards", job_id, timer,
        _do_initial_flashcards(lecture_id, job_id),
    )

    # ── Dashboard ready ───────────────────────────────────────────────────────
    await _update_job(
        job_id,
        status="dashboard_ready",
        step="deep_materials_generating",
        meta={"dashboard_ready_at": datetime.now().isoformat()},
    )
    logger.info("[pipeline] %s: *** DASHBOARD READY ***", lecture_id)

    # ── Stage 5: Deep path — parallel, failure-isolated ───────────────────────
    # All three can run concurrently; a failure in one does NOT cancel the others.
    await asyncio.gather(
        _run_isolated(
            "concept_enrichment", job_id, timer,
            _do_concept_enrichment(lecture_id, job_id, total_duration),
        ),
        _run_isolated(
            "deep_summaries", job_id, timer,
            _do_deep_summaries(lecture_id, job_id),
        ),
        _run_isolated(
            "full_flashcards_quiz", job_id, timer,
            _do_full_flashcards_and_quiz(lecture_id, job_id),
        ),
    )

    # ── Stage 6: Mind map (benefits from enriched concepts) ───────────────────
    await _run_isolated(
        "mindmap", job_id, timer,
        _do_mindmap(lecture_id, job_id),
    )

    # ── Done ──────────────────────────────────────────────────────────────────
    timing_summary = timer.summary()
    total_s = sum(e["duration_s"] for e in timing_summary)

    await _update_job(
        job_id,
        status="complete",
        step=None,
        meta={
            "pipeline_end":      datetime.now().isoformat(),
            "total_duration_s":  round(total_s, 2),
            "stage_timings":     timing_summary,
        },
    )
    await _finish_lecture(lecture_id, "completed")

    logger.info(
        "[pipeline] %s: COMPLETE in %.1fs  stages=%s",
        lecture_id,
        total_s,
        [(e["stage"], f"{e['duration_s']}s") for e in timing_summary],
    )


# ── Celery entry point ────────────────────────────────────────────────────────

@celery_app.task(name="app.jobs.tasks.process_lecture", bind=True, max_retries=2)
def process_lecture(self, lecture_id: str, job_id: str) -> dict:
    """Celery entry-point: run the async staged pipeline synchronously."""
    try:
        asyncio.run(_run_pipeline(lecture_id, job_id))
        return {"status": "completed", "lecture_id": lecture_id}
    except Exception as exc:
        logger.error("[celery] process_lecture failed for %s: %s", lecture_id, exc)
        try:
            asyncio.run(_update_job(job_id, status="failed", error=str(exc)))
            asyncio.run(_finish_lecture(lecture_id, "failed", str(exc)))
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
