import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TranscriptQuality(Base):
    """Per-lecture transcript quality record created by the ingestion pipeline."""

    __tablename__ = "transcript_quality"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )

    # Ingestion method
    method: Mapped[str] = mapped_column(String(30), nullable=False)  # "youtube_captions" | "whisper_fallback"
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality metrics
    confidence_avg: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_min: Mapped[float] = mapped_column(Float, nullable=False)
    noise_ratio: Mapped[float] = mapped_column(Float, default=0.0)   # 0–1 fraction of noise tokens

    # Coverage
    coverage_pct: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    gap_count: Mapped[int] = mapped_column(Integer, default=0)
    gap_locations: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [[start, end], ...]

    # Volume
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    segment_count: Mapped[int] = mapped_column(Integer, default=0)
    total_duration: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="transcript_quality")  # type: ignore[name-defined]  # noqa: F821
