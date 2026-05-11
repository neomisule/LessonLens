import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#7C3AED")
    icon: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # Use server_default only — avoids tz-naive/tz-aware mismatch with asyncpg
    # on TIMESTAMP WITHOUT TIME ZONE columns.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    lectures: Mapped[list["Lecture"]] = relationship("Lecture", back_populates="subject", cascade="all, delete-orphan", lazy="selectin")  # type: ignore[name-defined]  # noqa: F821
