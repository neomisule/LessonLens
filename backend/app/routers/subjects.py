from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectRead
from app.schemas.common import PaginatedResponse
import app.services.subject_service as svc

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("/", response_model=list[SubjectRead])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    return await svc.list_subjects(db)


@router.post("/", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
async def create_subject(payload: SubjectCreate, db: AsyncSession = Depends(get_db)):
    return await svc.create_subject(db, payload)


@router.get("/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: str, db: AsyncSession = Depends(get_db)):
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.patch("/{subject_id}", response_model=SubjectRead)
async def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return await svc.update_subject(db, subject, payload)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: str, db: AsyncSession = Depends(get_db)):
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    await svc.delete_subject(db, subject)
