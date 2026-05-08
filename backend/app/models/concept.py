import uuid
from sqlalchemy import String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.models.transcript import EMBEDDING_DIM


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core content
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list] = mapped_column(JSON, default=list)

    # Position in lecture
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp_end: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Classification
    importance: Mapped[str] = mapped_column(String(20), default="supporting")
    tags: Mapped[list] = mapped_column(JSON, default=list)

    # Evidence from transcript (grounding)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Learn mode metadata — computed by ConceptMapperAgent
    time_spent_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    exam_likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)      # ["concept_name", ...]
    related_concepts: Mapped[list] = mapped_column(JSON, default=list)   # ["concept_name", ...]
    evidence_timestamps: Mapped[list] = mapped_column(JSON, default=list)  # [{"ts": 45.0, "quote": "..."}, ...]

    # Embedding for similarity search
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="concepts")  # type: ignore[name-defined]  # noqa: F821
    flashcards: Mapped[list["Flashcard"]] = relationship("Flashcard", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
    mastery_records: Mapped[list["UserMastery"]] = relationship("UserMastery", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
    mindmap_nodes: Mapped[list["MindMapNode"]] = relationship("MindMapNode", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
