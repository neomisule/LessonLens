import asyncio
from datetime import datetime, timezone

from app.jobs.worker import celery_app
from app.database import async_session_factory
from app.models.lecture import Lecture
from app.models.processing import ProcessingJob
from app.orchestration.pipeline import build_pipeline


async def _run_pipeline(lecture_id: str, job_id: str) -> None:
    async with async_session_factory() as db:
        job: ProcessingJob | None = await db.get(ProcessingJob, job_id)
        lecture: Lecture | None = await db.get(Lecture, lecture_id)

        if not job or not lecture:
            return

        # Mark as started — agents will update current_step from here
        job.status = "processing"
        job.current_step = "downloading"
        lecture.processing_status = "processing"
        await db.commit()

    try:
        pipeline = build_pipeline()
        initial_state = {
            "lecture_id": lecture_id,
            "job_id": job_id,
            "youtube_url": lecture.youtube_url,
            "youtube_id": lecture.youtube_id,   # model field is youtube_id
        }
        final_state = await pipeline.ainvoke(initial_state)

        # Check for pipeline-level errors
        if final_state.get("error"):
            raise RuntimeError(final_state["error"])

        # Mark completed
        async with async_session_factory() as db:
            job = await db.get(ProcessingJob, job_id)
            lecture = await db.get(Lecture, lecture_id)
            if job:
                job.status = "completed"
                job.current_step = None
                job.completed_at = datetime.now(timezone.utc)
            if lecture:
                lecture.processing_status = "completed"
                lecture.processed_at = datetime.now(timezone.utc)
            await db.commit()

    except Exception as exc:
        async with async_session_factory() as db:
            job = await db.get(ProcessingJob, job_id)
            lecture = await db.get(Lecture, lecture_id)
            if job:
                job.status = "failed"
                if not job.error_message:
                    job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
            if lecture:
                lecture.processing_status = "failed"
                lecture.processing_error = str(exc)
            await db.commit()
        raise


@celery_app.task(name="app.jobs.tasks.process_lecture", bind=True, max_retries=2)
def process_lecture(self, lecture_id: str, job_id: str) -> dict:
    """Celery entry-point: run the async pipeline synchronously."""
    try:
        asyncio.run(_run_pipeline(lecture_id, job_id))
        return {"status": "completed", "lecture_id": lecture_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
