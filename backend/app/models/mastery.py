import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserMastery(Base):
    __tablename__ = "user_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=True, index=True)
    flashcard_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=True, index=True)
    mastery_level: Mapped[str] = mapped_column(String(20), default="unseen")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # SM-2 spaced repetition fields
    confidence: Mapped[str] = mapped_column(String(20), default="not_started")  # mastered|shaky|confused|not_started
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    next_review_interval_days: Mapped[int] = mapped_column(Integer, default=1)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="mastery_records")  # type: ignore[name-defined]  # noqa: F821
    concept: Mapped["Concept | None"] = relationship("Concept", back_populates="mastery_records")  # type: ignore[name-defined]  # noqa: F821
    flashcard: Mapped["Flashcard | None"] = relationship("Flashcard", back_populates="mastery_records")  # type: ignore[name-defined]  # noqa: F821
