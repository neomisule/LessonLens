import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Lecture(Base):
    __tablename__ = "lectures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=False)
    youtube_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())

    subject: Mapped["Subject"] = relationship("Subject", back_populates="lectures")  # type: ignore[name-defined]  # noqa: F821
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship("TranscriptSegment", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    semantic_segments: Mapped[list["SemanticSegment"]] = relationship("SemanticSegment", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    concepts: Mapped[list["Concept"]] = relationship("Concept", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    flashcards: Mapped[list["Flashcard"]] = relationship("Flashcard", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    summaries: Mapped[list["Summary"]] = relationship("Summary", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    mastery_records: Mapped[list["UserMastery"]] = relationship("UserMastery", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    mindmap_nodes: Mapped[list["MindMapNode"]] = relationship("MindMapNode", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    mindmap_edges: Mapped[list["MindMapEdge"]] = relationship("MindMapEdge", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship("ProcessingJob", back_populates="lecture", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
