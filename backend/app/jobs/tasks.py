import asyncio
from datetime import datetime, timezone

from app.jobs.worker import celery_app
from app.database import async_session_factory
from app.models.lecture import Lecture
from app.models.processing import ProcessingJob
from app.orchestration.pipeline import build_pipeline


async def _run_pipeline(lecture_id: str, job_id: str) -> None:
    async with async_session_factory() as db:
        # Mark job as downloading (first real step)
        job: ProcessingJob | None = await db.get(ProcessingJob, job_id)
        lecture: Lecture | None = await db.get(Lecture, lecture_id)

        if not job or not lecture:
            return

        job.status = "downloading"
        job.current_step = "transcript_extraction"
        lecture.processing_status = "processing"
        await db.commit()

        try:
            pipeline = build_pipeline()
            initial_state = {
                "lecture_id": lecture_id,
                "job_id": job_id,
                "youtube_url": lecture.youtube_url,
                "youtube_video_id": lecture.youtube_video_id or "",
            }
            await pipeline.ainvoke(initial_state)

            # Mark completed
            job.status = "completed"
            job.current_step = None
            job.completed_at = datetime.now(timezone.utc)
            lecture.processing_status = "completed"
            await db.commit()

        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            lecture.processing_status = "failed"
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
