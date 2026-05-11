import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, JSON, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Chapter(Base):
    """A named chapter / topic section within a lecture."""

    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    timestamp_start: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp_end: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Associated concept names (JSON list of strings)
    concept_names: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="chapters")  # type: ignore[name-defined]  # noqa: F821
