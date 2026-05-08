from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.processing import ProcessingJobRead
import app.services.lecture_service as svc

router = APIRouter(prefix="/jobs", tags=["processing"])


@router.get("/{job_id}", response_model=ProcessingJobRead)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await svc.get_processing_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return job
