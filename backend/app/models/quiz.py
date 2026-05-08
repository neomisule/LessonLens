import uuid
from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")

    # Revise Mode grounding fields
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="quiz_questions")  # type: ignore[name-defined]  # noqa: F821
    concept: Mapped["Concept | None"] = relationship("Concept")  # type: ignore[name-defined]  # noqa: F821
