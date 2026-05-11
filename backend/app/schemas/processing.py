from datetime import datetime
from pydantic import BaseModel


class ProcessingJobRead(BaseModel):
    id: str
    lecture_id: str
    status: str
    current_step: str | None
    steps_completed: list
    steps_total: int
    error_message: str | None
    progress_metadata: dict | None = None
    stage_errors: dict | None = None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
