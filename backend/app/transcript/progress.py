"""Progress reporting utilities for pipeline agents.

Each agent calls ProgressReporter to update the ProcessingJob row
in the database so the frontend can poll for live status.
"""
import logging
from datetime import datetime, timezone

from app.database import async_session_factory
from app.models.processing import ProcessingJob

logger = logging.getLogger(__name__)


class ProgressReporter:
    """
    Lightweight DB updater for pipeline job status.

    Usage inside an agent::

        reporter = ProgressReporter(job_id=state["job_id"])
        await reporter.set_step("downloading")
        # … do work …
        await reporter.complete_step("downloading", detail={"title": "…"})
        await reporter.set_step("transcribing")
    """

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self._completed: list[str] = []

    async def set_step(
        self,
        step: str,
        detail: dict | None = None,
    ) -> None:
        """Mark `step` as the currently active step without completing it."""
        async with async_session_factory() as db:
            job: ProcessingJob | None = await db.get(ProcessingJob, self.job_id)
            if not job:
                logger.warning("ProgressReporter: job %s not found", self.job_id)
                return

            job.current_step = step
            job.steps_completed = list(self._completed)
            if detail:
                meta = dict(job.progress_metadata or {})
                meta[step] = detail
                job.progress_metadata = meta

            await db.commit()

    async def complete_step(
        self,
        step: str,
        detail: dict | None = None,
    ) -> None:
        """Mark `step` as completed and persist to DB."""
        if step not in self._completed:
            self._completed.append(step)

        async with async_session_factory() as db:
            job: ProcessingJob | None = await db.get(ProcessingJob, self.job_id)
            if not job:
                return

            job.steps_completed = list(self._completed)
            if detail:
                meta = dict(job.progress_metadata or {})
                meta[step] = detail
                job.progress_metadata = meta

            await db.commit()

    async def fail(self, error: str) -> None:
        """Mark the job as failed with an error message."""
        async with async_session_factory() as db:
            job: ProcessingJob | None = await db.get(ProcessingJob, self.job_id)
            if not job:
                return
            job.status = "failed"
            job.error_message = error
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
