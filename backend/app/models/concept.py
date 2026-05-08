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
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance: Mapped[str] = mapped_column(String(20), default="supporting")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="concepts")  # type: ignore[name-defined]  # noqa: F821
    flashcards: Mapped[list["Flashcard"]] = relationship("Flashcard", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
    mastery_records: Mapped[list["UserMastery"]] = relationship("UserMastery", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
    mindmap_nodes: Mapped[list["MindMapNode"]] = relationship("MindMapNode", back_populates="concept")  # type: ignore[name-defined]  # noqa: F821
