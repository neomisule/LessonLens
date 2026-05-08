import uuid
from sqlalchemy import String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")
    tags: Mapped[list] = mapped_column(JSON, default=list)

    # Revise Mode fields
    question_type: Mapped[str] = mapped_column(String(20), default="surface")   # surface|deep|application
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp_end: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exam_likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="flashcards")  # type: ignore[name-defined]  # noqa: F821
    concept: Mapped["Concept | None"] = relationship("Concept", back_populates="flashcards")  # type: ignore[name-defined]  # noqa: F821
    mastery_records: Mapped[list["UserMastery"]] = relationship("UserMastery", back_populates="flashcard")  # type: ignore[name-defined]  # noqa: F821
