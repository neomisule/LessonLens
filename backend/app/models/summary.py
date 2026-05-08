import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id: Mapped[str] = mapped_column(String(36), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)

    # "brief" | "standard" | "detailed"
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON list of SummarySection dicts:
    # [{"heading": str, "content": str, "timestamp_start": float, "timestamp_end": float, "key_points": [str]}]
    sections: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    lecture: Mapped["Lecture"] = relationship("Lecture", back_populates="summaries")  # type: ignore[name-defined]  # noqa: F821
