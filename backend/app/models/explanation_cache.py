"""ExplanationCache model — stores generated alternative explanations.

Each row represents one (concept, style, language) explanation generated
by ConfusionRescueAgent.  The audio_cache_key column links to the on-disk
MP3 via the same SHA-256 key used by ElevenLabsClient.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ExplanationCache(Base):
    __tablename__ = "explanation_cache"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Source concept
    concept_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lecture_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Explanation parameters
    style: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    # Generated content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Audio cache key (SHA-256 used by ElevenLabsClient)
    # NULL means audio has not been generated for this explanation yet
    audio_cache_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_duration_ms: Mapped[int | None] = mapped_column(
        __import__("sqlalchemy").Integer(), nullable=True
    )

    generated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    concept: Mapped["Concept"] = relationship("Concept")  # type: ignore[name-defined]  # noqa: F821
