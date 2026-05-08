from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.lecture import Lecture
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectRead


async def list_subjects(db: AsyncSession) -> list[SubjectRead]:
    result = await db.execute(select(Subject).order_by(Subject.name))
    subjects = result.scalars().all()

    # Attach lecture counts via a single GROUP BY query
    count_result = await db.execute(
        select(Lecture.subject_id, func.count(Lecture.id).label("cnt"))
        .group_by(Lecture.subject_id)
    )
    counts: dict[str, int] = {row.subject_id: row.cnt for row in count_result}

    return [
        SubjectRead.model_validate(s).model_copy(update={"lecture_count": counts.get(s.id, 0)})
        for s in subjects
    ]


async def get_subject(db: AsyncSession, subject_id: str) -> Subject | None:
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def create_subject(db: AsyncSession, payload: SubjectCreate) -> Subject:
    subject = Subject(**payload.model_dump())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


async def update_subject(
    db: AsyncSession, subject: Subject, payload: SubjectUpdate
) -> Subject:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    await db.commit()
    await db.refresh(subject)
    return subject


async def delete_subject(db: AsyncSession, subject: Subject) -> None:
    await db.delete(subject)
    await db.commit()
