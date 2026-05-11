import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.processing import ProcessingJobRead
import app.services.lecture_service as svc

router = APIRouter(prefix="/jobs", tags=["processing"])

_TERMINAL = {"complete", "completed", "failed"}


@router.websocket("/{job_id}/ws")
async def job_ws(job_id: str, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    Push job status to the client every 500 ms until terminal state.
    4x more responsive than the previous 2-second poll.
    """
    await websocket.accept()
    try:
        last_status = None
        while True:
            job = await svc.get_processing_job(db, job_id)
            if job:
                # Only send when something changed (avoids redundant frames)
                current = job.status
                if current != last_status:
                    data = ProcessingJobRead.model_validate(job).model_dump(mode="json")
                    await websocket.send_json(data)
                    last_status = current
                if current in _TERMINAL:
                    break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.get("/{job_id}", response_model=ProcessingJobRead)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await svc.get_processing_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return job


@router.get("/{job_id}/debug")
async def get_job_debug(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns stage-level timing data stored in progress_metadata.

    Useful for diagnosing slow stages in production.
    Example response:
      {
        "job_id": "...",
        "status": "complete",
        "total_duration_s": 78.4,
        "stage_timings": [
          {"stage": "transcript_extracting", "duration_s": 18.2, "llm_calls": 0, "success": true},
          {"stage": "segmenting",            "duration_s": 4.1,  "llm_calls": 1, "success": true},
          ...
        ],
        "stage_errors": {"deep_summaries": "LLM timeout after 30s"}
      }
    """
    job = await svc.get_processing_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    meta = job.progress_metadata or {}
    return {
        "job_id":          job.id,
        "status":          job.status,
        "current_step":    job.current_step,
        "total_duration_s": meta.get("total_duration_s"),
        "pipeline_start":  meta.get("pipeline_start"),
        "pipeline_end":    meta.get("pipeline_end"),
        "dashboard_ready_at": meta.get("dashboard_ready_at"),
        "stage_timings":   meta.get("stage_timings", []),
        "stage_errors":    job.stage_errors or {},
        "steps_completed": job.steps_completed,
    }
