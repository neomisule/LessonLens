"""RevisionPlan — one spaced-repetition schedule entry per concept per lecture."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RevisionPlan(Base):
    __tablename__ = "revision_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    lecture_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    concept_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )

    # Human-readable context
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)     # why this is due
    priority: Mapped[int] = mapped_column(Integer, default=1)     # 1 = highest

    # Scheduling
    due_in_days: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Context
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    exam_likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[str] = mapped_column(String(20), default="not_started")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    lecture: Mapped["Lecture"] = relationship("Lecture")  # type: ignore[name-defined]  # noqa: F821
    concept: Mapped["Concept | None"] = relationship("Concept")  # type: ignore[name-defined]  # noqa: F821
