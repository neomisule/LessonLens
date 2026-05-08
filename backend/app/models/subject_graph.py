"""Subject-level concept graph models.

SubjectConcept — a canonical concept that appears across one or more lectures.
SubjectConceptLink — maps a per-lecture Concept to its canonical SubjectConcept.

Together these tables enable:
  - Recurring concept detection (frequency > 1)
  - Cross-lecture prerequisite chains
  - Weak-topic overlays (from aggregated mastery)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SubjectConcept(Base):
    """
    A canonical concept that recurs across lectures within a subject.

    frequency = number of lectures in which this concept name appears.
    cluster_label = normalized canonical form of the name.
    is_prerequisite = True if any lecture concept lists this as a prerequisite.
    avg_exam_likelihood = mean exam_likelihood across all linked concepts.
    avg_mastery = 0.0–1.0 derived from mastery records (computed by service).
    """
    __tablename__ = "subject_concepts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    cluster_label: Mapped[str] = mapped_column(String(300), nullable=False)  # normalized
    frequency: Mapped[int] = mapped_column(Integer, default=1)               # lecture count
    is_prerequisite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)       # appears in 2+ lectures
    avg_exam_likelihood: Mapped[float] = mapped_column(Float, default=0.5)
    avg_mastery: Mapped[float] = mapped_column(Float, default=0.0)           # 0=not_started, 1=mastered
    importance: Mapped[str] = mapped_column(String(20), default="supporting")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    subject: Mapped["Subject"] = relationship("Subject")  # type: ignore[name-defined]  # noqa: F821
    links: Mapped[list["SubjectConceptLink"]] = relationship(
        "SubjectConceptLink", back_populates="subject_concept", cascade="all, delete-orphan"
    )


class SubjectConceptLink(Base):
    """Links a per-lecture Concept row to its canonical SubjectConcept."""
    __tablename__ = "subject_concept_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject_concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subject_concepts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    lecture_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    subject_concept: Mapped["SubjectConcept"] = relationship(
        "SubjectConcept", back_populates="links"
    )
    concept: Mapped["Concept"] = relationship("Concept")  # type: ignore[name-defined]  # noqa: F821
    lecture: Mapped["Lecture"] = relationship("Lecture")  # type: ignore[name-defined]  # noqa: F821
