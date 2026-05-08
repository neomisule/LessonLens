import uuid
from sqlalchemy import String, Text, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

EMBEDDING_DIM = 1536


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_start: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp_end: Mapped[float] = mapped_column(Float, nullable=False)
    # Ingestion metadata
    source: Mapped[str] = mapped_column(String(30), default="youtube_captions", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="transcript_segments")  # type: ignore[name-defined]  # noqa: F821


class SemanticSegment(Base):
    __tablename__ = "semantic_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_start: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp_end: Mapped[float] = mapped_column(Float, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    # Segmentation metadata
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    topic_boundary_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="semantic_segments")  # type: ignore[name-defined]  # noqa: F821
