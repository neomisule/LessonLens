from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.lecture import LectureCreate, LectureRead
from app.schemas.processing import ProcessingJobRead
import app.services.lecture_service as svc

router = APIRouter(prefix="/lectures", tags=["lectures"])


@router.get("/", response_model=list[LectureRead])
async def list_lectures(subject_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.list_lectures(db, subject_id)


@router.post("/", response_model=LectureRead, status_code=status.HTTP_201_CREATED)
async def add_lecture(payload: LectureCreate, db: AsyncSession = Depends(get_db)):
    return await svc.add_lecture(db, payload)


@router.get("/{lecture_id}", response_model=LectureRead)
async def get_lecture(lecture_id: str, db: AsyncSession = Depends(get_db)):
    lecture = await svc.get_lecture(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return lecture


@router.post(
    "/{lecture_id}/analyze",
    response_model=ProcessingJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_lecture(lecture_id: str, db: AsyncSession = Depends(get_db)):
    lecture = await svc.get_lecture(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    if lecture.processing_status in ("processing", "completed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lecture is already {lecture.processing_status}",
        )
    job = await svc.start_processing(db, lecture)
    return job


@router.delete("/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lecture(lecture_id: str, db: AsyncSession = Depends(get_db)):
    lecture = await svc.get_lecture(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    await svc.delete_lecture(db, lecture)
