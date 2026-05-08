from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectRead
from app.schemas.common import PaginatedResponse
from app.schemas.subject_graph import (
    SubjectGraphRead,
    RecurringConceptRead,
    SubjectConceptRead,
    PrerequisiteChainRead,
)
import app.services.subject_service as svc
import app.services.subject_graph_service as graph_svc
from app.agents.subject_graph_agent import rebuild_subject_graph

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


# ── Subject-level intelligence ────────────────────────────────────────────────

@router.get("/{subject_id}/graph", response_model=SubjectGraphRead)
async def get_subject_graph(subject_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return the full subject-level concept graph.

    Nodes: one per lecture + one per canonical concept.
    Edges: belongs_to (concept→lecture) + prerequisite (concept→concept).
    Node colors encode mastery state (green=mastered, amber=in-progress, red=confused, gray=unseen).
    """
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return await graph_svc.get_subject_graph(db, subject_id)


@router.post("/{subject_id}/graph/rebuild", status_code=status.HTTP_202_ACCEPTED)
async def rebuild_graph(subject_id: str, db: AsyncSession = Depends(get_db)):
    """Force-rebuild the subject concept graph from all completed lectures."""
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    result = await rebuild_subject_graph(db, subject_id)
    return {"status": "rebuilt", **result}


@router.get("/{subject_id}/recurring", response_model=list[RecurringConceptRead])
async def get_recurring_concepts(subject_id: str, db: AsyncSession = Depends(get_db)):
    """Return concepts that appear across 2+ lectures in this subject."""
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return await graph_svc.get_recurring_concepts(db, subject_id)


@router.get("/{subject_id}/weak-topics", response_model=list[SubjectConceptRead])
async def get_weak_topics(
    subject_id: str,
    threshold: float = 0.3,
    db: AsyncSession = Depends(get_db),
):
    """
    Return concepts with average mastery below the threshold.
    These are the topics most in need of revision.
    """
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return await graph_svc.get_weak_topics(db, subject_id, threshold=threshold)


@router.get("/{subject_id}/prerequisites", response_model=list[PrerequisiteChainRead])
async def get_prerequisite_chains(subject_id: str, db: AsyncSession = Depends(get_db)):
    """Return prerequisite dependency chains across all lectures in this subject."""
    subject = await svc.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return await graph_svc.get_prerequisite_chains(db, subject_id)
