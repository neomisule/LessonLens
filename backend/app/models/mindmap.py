import uuid
from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MindMapNode(Base):
    __tablename__ = "mind_map_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    # Nullable subject_id for subject-level nodes
    subject_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    concept_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    node_type: Mapped[str] = mapped_column(String(20), default="leaf")  # root|branch|leaf|lecture
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Context for frontend overlay
    importance: Mapped[str] = mapped_column(String(20), default="supporting")     # core|supporting|supplemental
    exam_likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    timestamp_start: Mapped[float | None] = mapped_column(Float, nullable=True)

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="mindmap_nodes")  # type: ignore[name-defined]  # noqa: F821
    concept: Mapped["Concept | None"] = relationship("Concept", back_populates="mindmap_nodes")  # type: ignore[name-defined]  # noqa: F821


class MindMapEdge(Base):
    __tablename__ = "mind_map_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    source_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("mind_map_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("mind_map_nodes.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    edge_type: Mapped[str] = mapped_column(String(20), default="hierarchical")  # hierarchical|prerequisite|related|cross_lecture

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="mindmap_edges")  # type: ignore[name-defined]  # noqa: F821
