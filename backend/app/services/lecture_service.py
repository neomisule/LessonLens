import re
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lecture import Lecture
from app.models.processing import ProcessingJob
from app.schemas.lecture import LectureCreate, LectureUpdate


_YT_PATTERN = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_\-]{11})"
)


def _extract_youtube_id(url: str) -> str | None:
    match = _YT_PATTERN.search(url)
    return match.group(1) if match else None


async def list_lectures(db: AsyncSession, subject_id: str) -> list[Lecture]:
    result = await db.execute(
        select(Lecture)
        .where(Lecture.subject_id == subject_id)
        .order_by(Lecture.created_at.desc())
    )
    return list(result.scalars().all())


async def get_lecture(db: AsyncSession, lecture_id: str) -> Lecture | None:
    result = await db.execute(select(Lecture).where(Lecture.id == lecture_id))
    return result.scalar_one_or_none()


async def add_lecture(db: AsyncSession, payload: LectureCreate) -> Lecture:
    video_id = _extract_youtube_id(payload.youtube_url)
    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

    lecture = Lecture(
        subject_id=payload.subject_id,
        youtube_url=payload.youtube_url,
        youtube_id=video_id or "",           # model field is youtube_id
        title=payload.title or f"Lecture – {video_id or 'unknown'}",
        thumbnail_url=thumbnail,
        processing_status="pending",
    )
    db.add(lecture)
    await db.commit()
    await db.refresh(lecture)
    return lecture


async def start_processing(db: AsyncSession, lecture: Lecture) -> ProcessingJob:
    lecture.processing_status = "queued"
    job = ProcessingJob(
        lecture_id=lecture.id,
        status="queued",
        started_at=datetime.now(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Enqueue Celery task
    from app.jobs.tasks import process_lecture  # local import avoids circular import at startup
    process_lecture.delay(lecture.id, job.id)

    return job


async def get_processing_job(db: AsyncSession, job_id: str) -> ProcessingJob | None:
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    return result.scalar_one_or_none()


async def delete_lecture(db: AsyncSession, lecture: Lecture) -> None:
    await db.delete(lecture)
    await db.commit()
