import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    steps_completed: Mapped[list] = mapped_column(JSON, default=list)
    steps_total: Mapped[int] = mapped_column(Integer, default=7)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Per-stage error messages: {"stage_name": "error text", ...}
    # A stage can fail without failing the whole job (failure isolation).
    stage_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="processing_jobs")  # type: ignore[name-defined]  # noqa: F821
